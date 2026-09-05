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


def check_layout(page):
    # Streamlit scrolls inside stMain, so checking body alone misses overflow.
    for selector in ("body", '[data-testid="stMain"]', ".st-key-app_content", ".resp-visual"):
        assert page.locator(selector).evaluate_all(
            "els => els.every(el => el.scrollWidth <= el.clientWidth + 1)"
        ), f"Horizontal overflow: {selector}"
    if page.viewport_size["width"] >= 1024:
        assert page.locator(".resp-visual").evaluate_all("""els => els.every(el => {
            const tops = [...el.children].map(group => group.getBoundingClientRect().top);
            return Math.max(...tops) - Math.min(...tops) < 1;
        })"""), "Desktop answers must stay on one line"


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
            card = page.locator(".st-key-respostas_MT")
            field = card.frame_locator("iframe").get_by_label("Respostas MT", exact=True)
            expect(field).to_be_visible()
            assert field.evaluate("el => el.getBoundingClientRect().bottom <= window.innerHeight - 4"), "Input clipped by iframe"
            calculate = page.get_by_role("button", name="Calcular nota", exact=True)
            expect(calculate).to_be_disabled()

            field.press_sequentially("ABCDE", delay=130)
            expect(card.get_by_text("5/45 respostas · faltam 40", exact=True)).to_be_visible()
            expect(field).to_be_focused()
            field.press("Backspace")
            expect(card.get_by_text("4/45 respostas · faltam 41", exact=True)).to_be_visible()
            expect(field).to_be_focused()
            # Simulate a paste/autofill value change with no keyboard events.
            field.fill("ABCDE" * 9)
            expect(calculate).to_be_enabled()
            expect(card.get_by_text("45/45 respostas · completo", exact=True)).to_be_visible()
            field.press("Home")
            field.press("ArrowRight")
            field.press("Delete")
            field.press_sequentially("B")
            expect(card.get_by_text("45/45 respostas · completo", exact=True)).to_be_visible()
            expect(field).to_be_focused()
            assert field.evaluate("el => el.selectionStart") == 2

            # Same-length edit: blur flush while the debounce may still be pending.
            field.fill(final_answer)
            calculate.click()
            expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text(
                formatar_numero(expected["nota"]), timeout=30000,
            )
            assert "".join(card.locator(".resp-char").all_text_contents()) == final_answer
            download = page.get_by_role("button", name="Baixar Relatório PDF", exact=True)
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
            if width >= 768:
                assert page.locator(".grade-moldura").evaluate("""frame => {
                    const pie = [...document.querySelectorAll('.js-plotly-plot')]
                        .find(plot => plot.data?.[0]?.type === 'pie');
                    const grid = frame.getBoundingClientRect();
                    const chart = pie.getBoundingClientRect();
                    return Math.abs(grid.top + grid.height / 2 - chart.top - chart.height / 2) < 3;
                }"""), "Grid and donut must align vertically"
            assert cells.evaluate_all("""els => {
                const cells = els.map(el => el.getBoundingClientRect());
                return cells.every((a, i) => cells.slice(i + 1).every(b =>
                    a.right <= b.left + 1 || b.right <= a.left + 1 ||
                    a.bottom <= b.top + 1 || b.bottom <= a.top + 1));
            }"""), "Question cells overlap"
            columns = page.locator(".grade-questoes").evaluate(
                "el => getComputedStyle(el).gridTemplateColumns.split(' ').length"
            )
            assert columns == (5 if width <= 640 else 15)
            tables = page.locator('[data-testid="stDataFrame"]')
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
            page.get_by_test_id("stPopover").get_by_role("button").click()
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
