#!/usr/bin/env python3
"""Opt-in browser check against a running app; see streamlit_app/README.md.

Uses real iframe inputs, unlike AppTest. Viewport emulation does not test a
physical phone's keyboard. Playwright is an optional local test dependency.
"""
import argparse
from pathlib import Path
import sys
import tempfile

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from streamlit_app.config import AREAS_ENEM  # noqa: E402


def check_layout(page):
    # Streamlit scrolls inside stMain, so checking body alone misses overflow.
    for selector in ("body", '[data-testid="stMain"]', ".st-key-app_content", ".resumo", ".grade-painel", ".diagnostico-grupo"):
        assert page.locator(selector).evaluate_all(
            "els => els.every(el => el.scrollWidth <= el.clientWidth + 1)"
        ), f"Horizontal overflow: {selector}"
    # The bar scale stops at 1000; some MT tests go beyond it.
    assert page.locator(".resumo-barra").evaluate_all(
        "els => els.every(el => el.firstElementChild.getBoundingClientRect().width <= el.getBoundingClientRect().width + 0.5)"
    ), "Score bar wider than its track"


def check_frame(frame, label):
    """The iframe shows the whole field and status line, without inner scroll."""
    assert frame.locator("#status").evaluate(
        "el => el.getBoundingClientRect().bottom <= window.innerHeight"
    ), f"{label}: field clipped by iframe"


def check_year_changes(browser, url, *, delayed_html=False):
    """All four real inputs survive reordered cards and slow document parsing."""
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    if delayed_html:
        # Pause parsing before the body, as a slow/chunked response can do.
        # Previously main.js announced readiness from <head>; the first render
        # accessed missing DOM nodes and left the iframe at zero height.
        def delay_document(route):
            response = route.fetch()
            route.fulfill(response=response, body=response.text().replace(
                '<body id="root">',
                '<script src="./test-parser-delay.js"></script><body id="root">',
            ))

        def release_parser(route):
            page.wait_for_timeout(1000)
            route.fulfill(body="", content_type="application/javascript")

        page.route("**/component/**/index.html?*", delay_document)
        page.route("**/test-parser-delay.js", release_parser)

    answers = {"CH": "A" * 45, "CN": "B" * 45, "LC": "C" * 45, "MT": "D" * 45}
    page.goto(url)
    for step, year in enumerate((2023, 2011, 2023, 2011)):
        year_input = page.locator(".st-key-ano_prova").get_by_role("combobox")
        year_input.scroll_into_view_if_needed()
        year_input.click()        # the filtered list only opens after a click
        year_input.fill(str(year))
        page.get_by_role("option", name=str(year), exact=True).click()
        first_area = "CH" if year == 2011 else "LC"
        first = page.locator(f".st-key-respostas_{first_area}").frame_locator("iframe")
        expect(first.locator(".num").first).to_have_text("1")
        for area, answer in answers.items():
            frame = page.locator(f".st-key-respostas_{area}").frame_locator("iframe")
            field = frame.get_by_label(f"Respostas {area}", exact=True)
            expect(field).to_be_visible()
            check_frame(frame, f"{year} {area}")
            if step == 0:
                field.fill(answer)
            else:
                expect(field).to_have_value(answer)
                # Check that the restored input still sends edits to Python.
                field.fill(answer[:-1])
                expect(page.get_by_text(f"Falta 1 resposta em {AREAS_ENEM[area]}.", exact=False)).to_be_visible()
                field.fill(answer)
            expect(frame.locator("#contador")).to_have_text("45/45 respostas · completo")
        expect(page.get_by_role("button", name="Calcular nota", exact=True)).to_be_enabled()
    assert not errors, errors
    page.close()
    print(f"PASS year changes: visibility, retained answers, editing (delayed HTML={delayed_html})", flush=True)


def check_composition(browser, url):
    """Android keyboards type through IME composition, not plain insertText."""
    page = browser.new_page(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url)
    frame = page.locator(".st-key-respostas_MT").frame_locator("iframe")
    field = frame.get_by_label("Respostas MT", exact=True)
    field.scroll_into_view_if_needed()
    cdp = page.context.new_cdp_session(page)

    def compose(text):
        for k in range(1, len(text) + 1):
            cdp.send("Input.imeSetComposition", {"text": text[:k], "selectionStart": k, "selectionEnd": k})
        cdp.send("Input.insertText", {"text": text})

    def tap(index):
        box = frame.locator(".cel").nth(index).bounding_box()
        page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    tap(0)
    compose("abfc")
    expect(field).to_have_value("ABC")
    expect(frame.locator("#posicao")).to_have_text("“f” não é alternativa · use A a E ou ponto")
    tap(7)                        # an empty question ahead
    compose("d")
    expect(field).to_have_value("ABC\u00a0\u00a0\u00a0\u00a0D")
    tap(1)                        # replace, then keep replacing
    compose("e")
    compose("e")
    expect(field).to_have_value("AEE\u00a0\u00a0\u00a0\u00a0D")
    field.blur()
    expect(page.get_by_text("Faltam 41 respostas em Matemática.", exact=False)).to_be_visible()
    assert not errors, errors
    page.close()
    print("PASS composition: skipped question, replace, invalid letter", flush=True)


def run(url, executable, output):
    from streamlit_app.calculador import CalculadorEnem
    from tri_enem.formatacao import formatar_numero

    final_answer = "ABCDE" * 8 + "ABCDB"
    expected = CalculadorEnem().calcular_area(
        ano=2023, area="MT", respostas=final_answer,
        cor="azul", tipo_aplicacao="1a_aplicacao",
    )
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**({"executable_path": executable} if executable else {}))
        check_year_changes(browser, url)
        check_year_changes(browser, url, delayed_html=True)
        check_composition(browser, url)
        for width in (360, 390, 768, 1024, 1440):
            page = browser.new_page(viewport={"width": width, "height": 900},
                                    has_touch=width < 768, is_mobile=width < 768)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url)
            ano = page.locator(".st-key-ano_prova").get_by_role("combobox")
            # Scroll first: the implicit click-scroll closes the dropdown.
            ano.scroll_into_view_if_needed()
            ano.click()
            page.get_by_role("option", name="2023", exact=True).click()
            frame = page.locator(".st-key-respostas_MT").frame_locator("iframe")
            field = frame.get_by_label("Respostas MT", exact=True)
            counter = frame.locator("#contador")
            expect(field).to_be_visible()
            check_frame(frame, f"{width}px")
            calculate = page.get_by_role("button", name="Calcular nota", exact=True)
            expect(calculate).to_be_disabled()

            field.press_sequentially("ABCDE", delay=130)
            expect(counter).to_have_text("5/45 respostas · faltam 40")
            expect(field).to_be_focused()
            field.press("Backspace")
            expect(counter).to_have_text("4/45 respostas · faltam 41")
            expect(field).to_be_focused()
            # Simulate a paste/autofill value change with no keyboard events.
            field.fill("ABCDE" * 9)
            expect(calculate).to_be_enabled()
            expect(counter).to_have_text("45/45 respostas · completo")
            field.press("Control+Home")  # Home alone stops at the start of the visual row
            field.press("ArrowRight")
            field.press("Delete")
            field.press_sequentially("B")
            expect(counter).to_have_text("45/45 respostas · completo")
            expect(field).to_be_focused()
            assert field.evaluate("el => el.selectionStart") == 2

            # Same-length edit: blur flush while the debounce may still be pending.
            field.fill(final_answer)
            calculate.click()
            expect(page.locator(".resumo-media strong")).to_have_text(
                formatar_numero(expected["nota"]), timeout=30000,
            )
            expect(field).to_have_value(final_answer)
            download = page.get_by_role("button", name="Baixar relatório PDF")
            expect(download).to_be_visible()
            with page.expect_download() as event:
                download.click()
            downloaded = event.value
            pdf = Path(downloaded.path()).read_bytes()
            assert pdf.startswith(b"%PDF-") and pdf.rstrip().endswith(b"%%EOF")
            downloaded.save_as(output / f"resultado-{width}.pdf")

            # Expand the actual area, not the nested precision disclosure.
            page.locator('[data-testid="stExpander"] summary').filter(has_text="Matemática").click()
            cells = page.locator(".questao")
            expect(cells).to_have_count(45)
            expect(cells.first).to_be_visible()
            # Let the native expander finish opening before checking geometry.
            page.wait_for_function("""() => {
                const grid = document.querySelector('.grade-questoes');
                return grid?.closest('details')?.getBoundingClientRect().height > 800;
            }""")
            check_layout(page)
            expect(page.locator('[data-testid="stSidebar"]')).to_have_count(0)
            assert cells.evaluate_all("""els => {
                const cells = els.map(el => el.getBoundingClientRect());
                return cells.every((a, i) => cells.slice(i + 1).every(b =>
                    a.right <= b.left + 1 || b.right <= a.left + 1 ||
                    a.bottom <= b.top + 1 || b.bottom <= a.top + 1));
            }"""), "Question cells overlap"
            columns = page.locator(".grade-questoes").evaluate(
                "el => getComputedStyle(el).gridTemplateColumns.split(' ').length"
            )
            assert columns == (9 if width < 768 else 15)
            if width < 768:
                assert page.locator(".grade-painel").bounding_box()["height"] < 310
            tables = page.locator(".diagnostico-grupo")
            expect(page.locator('[data-testid="stDataFrame"]')).to_have_count(0)
            for group in tables.all():
                count = int(group.locator(".diagnostico-contagem").inner_text())
                expect(group.locator("tbody tr")).to_have_count(count)
                scroll = group.locator(".questoes-scroll")
                if count:
                    scroll.scroll_into_view_if_needed()
                    scroll.evaluate("el => el.scrollTop = el.scrollHeight")
                    expect(group.locator("tbody tr").last).to_be_in_viewport()
                    scroll.evaluate("el => el.scrollTop = 0")
            assert page.locator(".grade-painel").evaluate("""el => {
                const box = el.getBoundingClientRect();
                const parent = el.parentElement.getBoundingClientRect();
                return Math.abs(box.left + box.width / 2 - parent.left - parent.width / 2) < 2;
            }"""), "Question overview must be centered"
            first, second = tables.nth(0).bounding_box(), tables.nth(1).bounding_box()
            if width >= 768:
                assert second["x"] > first["x"] + first["width"] - 1
                assert abs(second["y"] - first["y"]) < 5
            else:
                assert second["y"] >= first["y"] + first["height"]
            assert page.locator(".js-plotly-plot").evaluate_all("""plots => plots.every(plot =>
                plot.data?.[0]?.type === 'pie' ||
                (plot.layout.dragmode === false && plot.layout.xaxis.fixedrange && plot.layout.yaxis.fixedrange)
            )"""), "Chart zoom must be disabled"
            if width <= 640:
                scroll = page.locator(".st-key-impacto_scroll_MT")
                scroll.scroll_into_view_if_needed()
                scroll.hover()
                page.mouse.wheel(220, 0)
                page.wait_for_function("document.querySelector('.st-key-impacto_scroll_MT').scrollLeft > 0")
            page.get_by_text("Grade de Questões", exact=True).scroll_into_view_if_needed()
            page.screenshot(path=str(output / f"resultados-{width}.png"), animations="disabled")
            tables.first.scroll_into_view_if_needed()
            page.screenshot(path=str(output / f"tabelas-{width}.png"), animations="disabled")
            field.scroll_into_view_if_needed()
            page.screenshot(path=str(output / f"respostas-{width}.png"))

            # Keyboard focus crosses the iframe, and editing invalidates output.
            field.focus()
            field.press("Tab")
            expect(field).not_to_be_focused()
            field.fill("A")
            expect(download).to_have_count(0)
            expect(calculate).to_be_disabled()
            page.get_by_test_id("stPopover").filter(has_text="Sobre o cálculo").get_by_role("button").click()
            expect(page.get_by_text("Modelo Logístico de 3 Parâmetros (ML3)", exact=True)).to_be_visible()
            page.keyboard.press("Escape")
            assert not errors, errors
            print(f"PASS {width}px: typing, paste, focus, calculation, PDF, layout", flush=True)
            page.close()
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument("--executable", help="Optional existing Chromium executable")
    parser.add_argument("--output", type=Path, default=Path(tempfile.gettempdir()) / "enem-browser-smoke")
    args = parser.parse_args()
    run(args.url, args.executable, args.output)
