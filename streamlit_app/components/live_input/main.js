// Adapted from streamlit-keyup 0.3.0 (Zachary Blackwood); see LICENSE.
// Folha de respostas: a textarea guarda sempre um caractere por questão
// ("_" = sem resposta) e recebe teclado, colar e desfazer; a camada atrás
// desenha números, letras e cursor. Toda edição sobrescreve questões, nunca
// desloca as seguintes.
const TOTAL = 45, BLOCO = 5, LETRAS = "ABCDE.*", VAZIA = "_";
const VAZIO = VAZIA.repeat(TOTAL);
const NUM = 15, LIN = 28, ENTRE = 8;   // px: números, letras, entre linhas
const PASSO = NUM + LIN + ENTRE;
const MARGEM = 2;                      // px: folga das faixas na primeira e na última linha
const CELULA_MAX = 30;
const TOQUE = matchMedia("(pointer: coarse)").matches;
const DESCRICAO = {[VAZIA]: "sem resposta", ".": "em branco", "*": "dupla marcação"};
let initialized = false;
let timer;
let lastSent;
let frameHeight = 0;
let inicio = 1;
let geo = {};
let modelo = VAZIO;        // valor aceito; a textarea só diverge dele numa edição nativa
let previa = null;         // {valor, cursor} durante a composição do teclado (Android)
let composicao = null;     // seleção no início da composição
let antes = {ini: 0, fim: 0};  // última seleção com a textarea igual ao modelo
let digitou = false;       // Backspace logo após digitar apaga a anterior
let focadoAntes = false;
let ponteiro = false;      // o foco veio de um toque ou clique no campo
let retomar = true;        // saiu do campo (não só da janela): o foco volta de onde parou
let alvo = null;           // questão escolhida pelo clique ou toque em andamento
let toque = null;          // questão e hora do último toque, para o toque longo
let hover = null;
let colada = new Set();
let aviso = "", avisoTimer;
let flush = () => {};
let agendar = () => {};

const $ = id => document.getElementById(id);
const ta = () => $("input_box");
const paraDentro = v => [...String(v || "").toUpperCase()].slice(0, TOTAL)
  .map(c => LETRAS.includes(c) ? c : VAZIA).join("").padEnd(TOTAL, VAZIA);
const paraFora = v => v.replace(/_+$/, "");
const respondidas = v => [...v].filter(c => c !== VAZIA).length;

// Retoma depois da última resposta; com a Q45 respondida, na primeira vazia.
function continuar(v = modelo) {
  const fim = paraFora(v).length;
  if (fim < TOTAL) return fim;
  const vazia = v.indexOf(VAZIA);
  return vazia < 0 ? TOTAL : vazia;
}

function resizeFrame() {
  const height = Math.ceil(document.body.getBoundingClientRect().height) + 4;
  if (height !== frameHeight) {
    frameHeight = height;
    Streamlit.setFrameHeight(height);
  }
}

// Mesmas fontes da página: o iframe tem a origem do app.
function herdarFontes() {
  try {
    const regras = [];
    for (const folha of parent.document.styleSheets) {
      let lista;
      try { lista = folha.cssRules; } catch (e) { continue; }
      for (const r of lista) {
        if (r.type !== 5 || !/Source (Sans|Code Pro)/.test(r.style.getPropertyValue("font-family"))) continue;
        const base = folha.href || parent.location.href;
        regras.push(r.cssText.replace(/url\("?([^")]+)"?\)/g, (_, u) => `url("${new URL(u, base)}")`));
      }
    }
    if (regras.length) document.head.appendChild(Object.assign(document.createElement("style"), {textContent: regras.join("\n")}));
  } catch (e) { /* sem acesso à página: fontes do sistema */ }
}

function larguraCaractere(el) {
  const medida = document.createElement("span");
  medida.style.cssText = "position:absolute;visibility:hidden;white-space:pre";
  medida.style.font = getComputedStyle(el).font;
  medida.textContent = "M".repeat(20);
  document.body.appendChild(medida);
  const largura = medida.getBoundingClientRect().width / 20;
  medida.remove();
  return largura;
}

function construir() {
  const camada = $("camada");
  const criar = classe => camada.appendChild(Object.assign(document.createElement("div"), {className: classe}));
  for (let b = 0; b < TOTAL / BLOCO; b++) criar(b % 2 ? "faixa faixa--par" : "faixa");
  for (let i = 0; i < TOTAL; i++) criar("cel");
  for (let i = 0; i < TOTAL; i++) criar("num");
}

// Linhas com blocos inteiros: 45, 25+20, 15×3 ou 10×4+5, o que couber.
// No toque, células de pelo menos 28 px para acertar a questão com o dedo.
function layout(forcar = false) {
  const area = ta(), folha = $("folha");
  const disponivel = $("caixa").clientWidth - 20;  // padding da caixa
  if (!forcar && disponivel === geo.disponivel) return;
  const ch = larguraCaractere(area);
  const minimo = Math.max(ch + 7, TOQUE ? 28 : 20);
  const porLinha = [45, 25, 15, 10].find(n => disponivel / n >= minimo) || 10;
  const cel = Math.min(disponivel / porLinha, CELULA_MAX);
  const linhas = Math.ceil(TOTAL / porLinha);
  const espaco = cel - ch;
  geo = {cel, porLinha, disponivel};
  // O texto da textarea fica invisível, mas alinhado às células: assim as
  // alças de seleção e a janela do teclado aparecem na questão certa.
  Object.assign(area.style, {
    letterSpacing: `${espaco}px`, lineHeight: `${PASSO}px`,
    paddingLeft: `${espaco / 2}px`, paddingTop: `${MARGEM + NUM + LIN / 2 - PASSO / 2}px`,
    width: `${porLinha * cel + cel / 2}px`, height: `${linhas * PASSO}px`,
  });
  Object.assign(folha.style, {width: `${porLinha * cel}px`, height: `${linhas * PASSO - ENTRE + 2 * MARGEM}px`});
  const pos = i => ({x: (i % porLinha) * cel, y: Math.floor(i / porLinha) * PASSO + MARGEM});
  const camada = $("camada");
  camada.querySelectorAll(".cel").forEach((el, i) => {
    const {x, y} = pos(i);
    Object.assign(el.style, {left: `${x + 1}px`, top: `${y + NUM}px`, width: `${cel - 2}px`, height: `${LIN}px`});
  });
  camada.querySelectorAll(".num").forEach((el, i) => {
    const {x, y} = pos(i);
    Object.assign(el.style, {left: `${x - 6}px`, top: `${y}px`, width: `${cel + 12}px`});
  });
  camada.querySelectorAll(".faixa").forEach((el, b) => {
    const {x, y} = pos(b * BLOCO);
    Object.assign(el.style, {left: `${x}px`, top: `${y - MARGEM}px`, width: `${BLOCO * cel}px`, height: `${NUM + LIN + 2 * MARGEM}px`});
  });
  resizeFrame();
}

function celulaEm(event) {
  const caixa = $("folha").getBoundingClientRect();
  const col = Math.floor((event.clientX - caixa.left) / geo.cel);
  const lin = Math.floor((event.clientY - caixa.top - MARGEM) / PASSO);
  if (col < 0 || col >= geo.porLinha || lin < 0) return null;
  const i = lin * geo.porLinha + col;
  return i < TOTAL ? i : null;
}

function avisar(texto) {
  aviso = texto;
  clearTimeout(avisoTimer);
  if (texto) avisoTimer = setTimeout(() => { aviso = ""; pintar(); }, 3000);
  pintar();
}

function pintar() {
  const area = ta();
  const foco = document.activeElement === area;
  const v = previa ? previa.valor : modelo;
  let [ini, fim] = previa ? [previa.cursor, previa.cursor] : [area.selectionStart, area.selectionEnd];
  if (!composicao && area.value === modelo) antes = {ini, fim};
  // Clique em andamento: mostra a questão escolhida, não o cursor nativo.
  if (alvo !== null && ini === fim) ini = fim = alvo;
  const atual = foco && ini === fim && ini < TOTAL ? ini : null;
  const sel = foco && fim > ini;
  $("camada").querySelectorAll(".cel").forEach((el, i) => {
    const c = v[i];
    const texto = c === VAZIA ? "" : c;
    if (el.textContent !== texto) el.textContent = texto;
    el.className = "cel"
      + (c === VAZIA ? " cel--vazia" : c === "." ? " cel--branco" : "")
      + (i === atual ? " cel--atual" : "")
      + (sel && i >= ini && i < fim ? " cel--sel" : "")
      + (colada.has(i) ? " cel--colada" : "");
  });
  $("camada").querySelectorAll(".num").forEach((el, i) => {
    const texto = String(inicio + i);
    if (el.textContent !== texto) el.textContent = texto;
    el.className = "num"
      + (i % BLOCO === 0 ? " num--bloco" : "")
      + (i === hover ? " num--hover" : "")
      + (i === atual || (sel && i >= ini && i < fim) ? " num--ativo" : "");
  });
  const feitas = respondidas(v);
  const contador = $("contador");
  contador.className = feitas === TOTAL ? "completo" : "";
  contador.textContent = feitas === 0 ? `0/${TOTAL} respostas`
    : feitas === TOTAL ? `${TOTAL}/${TOTAL} respostas · completo`
    : `${feitas}/${TOTAL} respostas · faltam ${TOTAL - feitas}`;
  const posicao = $("posicao");
  posicao.className = aviso ? "aviso" : "";
  posicao.textContent = aviso
    || (atual !== null ? `Questão ${inicio + atual}`
      : sel && fim - ini > 1 ? `Questões ${inicio + ini}–${inicio + fim - 1}`
      : sel ? `Questão ${inicio + ini}`
      : foco && ini >= TOTAL ? "Fim da prova"
      : "");
  // Leitor de tela: a questão e o que está marcado nela.
  const fala = aviso || (atual !== null ? `Questão ${inicio + atual}, ${DESCRICAO[v[atual]] || `resposta ${v[atual]}`}` : "");
  if ($("anuncio").textContent !== fala) $("anuncio").textContent = fala;
}

// Grava o valor numa edição só; execCommand mantém o desfazer nativo.
function escrever(novo, cursor) {
  const area = ta(), v = area.value;
  modelo = novo;
  previa = null;
  if (v !== novo) {
    let ok = false;
    if (v.length === TOTAL) {
      let p = 0, q = TOTAL;
      while (v[p] === novo[p]) p++;
      while (v[q - 1] === novo[q - 1]) q--;
      area.setSelectionRange(p, q);
      try { ok = document.execCommand("insertText", false, novo.slice(p, q)); } catch (e) { ok = false; }
    }
    if (!ok || area.value !== novo) area.value = novo;
  }
  area.setSelectionRange(cursor, cursor);
  if (aviso) avisar("");
  pintar();
  agendar();
}

function irPara(ini, fim = ini) {
  ta().setSelectionRange(ini, fim);
  digitou = false;
  if (aviso) avisar(""); else pintar();
}

function destacar(indices) {
  colada = new Set(indices);
  setTimeout(() => { colada = new Set(); pintar(); }, 650);
}

const recusar = letras => avisar(`“${[...new Set(letras)].join("")}” não é alternativa · use A a E ou ponto`);

// Grava letras a partir da questão ini, por cima do que houver.
function gravar(letras, ini) {
  if (ini >= TOTAL) {
    avisar(respondidas(modelo) === TOTAL ? "Prova completa · toque numa questão para trocar"
      : "Fim da prova · toque numa questão para continuar");
    return 0;
  }
  const v = [...modelo];
  const entra = letras.slice(0, TOTAL - ini);
  entra.forEach((c, k) => { v[ini + k] = c; });
  escrever(v.join(""), ini + entra.length);
  return entra.length;
}

// Digitar: minúscula vira maiúscula e espaço vira ponto (em branco). Com
// várias questões selecionadas, escreve na primeira e mantém as outras.
function digitar(dado) {
  const letras = [...dado.toUpperCase().replace(/\s/g, ".")];
  const validas = letras.filter(c => LETRAS.includes(c));
  const recusadas = letras.filter(c => !LETRAS.includes(c));
  if (validas.length) {
    const entrou = gravar(validas, ta().selectionStart);
    if (!entrou) return;
    digitou = true;
    if (!recusadas.length && entrou < validas.length) avisar(`Só ${entrou} de ${validas.length} letras cabiam`);
  }
  if (recusadas.length) recusar(recusadas);
}

// Backspace logo após digitar apaga a questão anterior; numa questão escolhida
// com resposta, apaga a própria. Delete apaga a questão do cursor. Com várias
// selecionadas, apaga todas. Nada se desloca.
function apagar(paraTras) {
  const area = ta(), v = [...modelo];
  const [ini, fim] = [area.selectionStart, area.selectionEnd];
  let de = ini, ate = fim;
  if (fim === ini) {
    if (!paraTras || (!digitou && ini < TOTAL && v[ini] !== VAZIA)) ate = ini + 1;
    else if (ini > 0) de = ini - 1;
  }
  ate = Math.min(ate, TOTAL);
  for (let k = de; k < ate; k++) v[k] = VAZIA;
  escrever(v.join(""), de);
  digitou = false;
}

// Colar: aceita 45 letras seguidas, com espaços, ou numeradas ("46-A, 47-B").
function colar(texto) {
  const area = ta();
  const pares = [...texto.matchAll(/(\d{1,3})\s*[-–—.:)=]?\s*([A-Ea-e*])(?![A-Za-z])/g)];
  if (pares.length >= 3) {
    const v = [...modelo];
    const usadas = new Set();
    for (const [, numero, letra] of pares) {
      const q = Number(numero);
      const i = q >= inicio && q < inicio + TOTAL ? q - inicio : q >= 1 && q <= TOTAL ? q - 1 : -1;
      if (i < 0) continue;
      v[i] = letra.toUpperCase();
      usadas.add(i);
    }
    if (usadas.size) {
      destacar(usadas);
      escrever(v.join(""), continuar(v.join("")));
      digitou = true;
      avisar(`${usadas.size} respostas coladas pelo número da questão`);
      return;
    }
  }
  const limpo = [...texto.toUpperCase().replace(/[\s,;|]+/g, "")];
  const letras = limpo.filter(c => LETRAS.includes(c) || c === VAZIA);
  const ignorados = limpo.filter(c => !LETRAS.includes(c) && c !== VAZIA);
  if (!letras.length) { avisar("Nada para colar · use letras de A a E"); return; }
  // Uma folha inteira vai desde a primeira questão; menos, a partir do cursor.
  const ini = letras.length >= TOTAL ? 0 : area.selectionStart;
  const entrou = gravar(letras, ini);
  if (!entrou) return;
  digitou = true;
  destacar(Array.from({length: entrou}, (_, k) => ini + k));
  pintar();
  if (ignorados.length) avisar(`Ignorado ao colar: ${[...new Set(ignorados)].join(" ")}`);
  else if (entrou < letras.length) avisar(`Só ${entrou} de ${letras.length} letras cabiam`);
}

// Edição que o navegador já aplicou (composição, teclado sem beforeinput
// cancelável): acha o trecho trocado, ancorado no cursor de antes, e o refaz
// sobrescrevendo. Devolve o valor e o cursor resultantes.
function reconciliar(depois, ini) {
  const v = modelo, max = Math.min(v.length, depois.length);
  let p = 0, s = 0;
  while (p < max && p < ini && v[p] === depois[p]) p++;
  while (s < max - p && v[v.length - 1 - s] === depois[depois.length - 1 - s]) s++;
  const novo = [...depois.slice(p, depois.length - s).toUpperCase().replace(/\s/g, ".")];
  const letras = novo.filter(c => LETRAS.includes(c) || c === VAZIA);
  const resultado = [...v];
  for (let k = p; k < v.length - s; k++) resultado[k] = VAZIA;
  letras.slice(0, TOTAL - p).forEach((c, k) => { resultado[p + k] = c; });
  return {
    valor: resultado.join(""),
    cursor: Math.min(p + letras.length, TOTAL),
    recusadas: novo.filter(c => !LETRAS.includes(c) && c !== VAZIA),
    digitou: letras.length > 0,
  };
}

function aceitarNativo(ini) {
  const area = ta(), r = reconciliar(area.value, ini);
  area.value = r.valor;
  modelo = r.valor;
  previa = null;
  area.setSelectionRange(r.cursor, r.cursor);
  digitou = r.digitou;
  if (r.recusadas.length) recusar(r.recusadas);
  pintar();
  agendar();
}

function iniciar(args) {
  const {label, value, debounce} = args;
  const area = ta();
  $("label").textContent = label;
  modelo = paraDentro(value);
  area.value = modelo;
  area.setSelectionRange(0, 0);
  lastSent = paraFora(modelo);
  herdarFontes();
  construir();
  flush = () => {
    clearTimeout(timer);
    const valor = paraFora(previa ? previa.valor : modelo);
    if (valor !== lastSent) {
      lastSent = valor;
      Streamlit.setComponentValue(valor);
    }
  };
  agendar = () => { clearTimeout(timer); timer = setTimeout(flush, debounce); };

  area.addEventListener("beforeinput", event => {
    const tipo = event.inputType;
    if (event.isComposing || tipo === "insertCompositionText") return;
    if (tipo === "historyUndo" || tipo === "historyRedo") return;  // edições do mesmo tamanho
    antes = {ini: area.selectionStart, fim: area.selectionEnd};
    if (!event.cancelable) return;  // o evento input reconcilia
    event.preventDefault();
    const dado = event.data ?? event.dataTransfer?.getData("text/plain") ?? "";
    if (tipo === "insertFromPaste" || tipo === "insertFromDrop") colar(dado);
    else if (tipo.startsWith("insert") && dado) digitar(dado);
    else if (tipo === "insertLineBreak" || tipo === "insertParagraph") area.blur();
    else if (tipo.startsWith("delete") && tipo !== "deleteByDrag") apagar(!tipo.includes("Forward"));
  });
  area.addEventListener("input", event => {
    if (composicao) {
      const r = reconciliar(area.value, composicao.ini);
      previa = {valor: r.valor, cursor: r.cursor};
    } else if (area.value !== modelo) {
      const tipo = event.inputType || "";
      const valido = area.value.length === TOTAL && paraDentro(area.value) === area.value;
      if (tipo.startsWith("history") && valido) {
        modelo = area.value;
        area.setSelectionRange(area.selectionStart, area.selectionStart);
      } else {
        aceitarNativo(antes.ini);
        return;
      }
    }
    pintar();
    agendar();
  });
  area.addEventListener("compositionstart", () => {
    composicao = {ini: area.selectionStart};
  });
  area.addEventListener("compositionend", () => {
    const {ini} = composicao;
    composicao = null;
    if (area.value !== modelo) aceitarNativo(ini);
    else { previa = null; pintar(); }
  });
  area.addEventListener("cut", event => {
    const [s, f] = [area.selectionStart, area.selectionEnd];
    event.preventDefault();
    if (s === f) return;
    event.clipboardData?.setData("text/plain", modelo.slice(s, f));
    apagar(true);
  });
  area.addEventListener("paste", event => {
    event.preventDefault();
    colar(event.clipboardData ? event.clipboardData.getData("text") : "");
  });
  for (const tipo of ["dragstart", "drop"]) area.addEventListener(tipo, event => event.preventDefault());

  // Tocar ou clicar escolhe a questão; o primeiro toque num campo vazio
  // começa pela primeira. A escolha vale desde o pointerdown, para o
  // destaque não passar pelo cursor nativo. Arrastar seleciona várias.
  const destino = event => {
    const i = celulaEm(event);
    return i === null || (!focadoAntes && modelo === VAZIO) ? continuar() : i;
  };
  area.addEventListener("pointerdown", event => {
    focadoAntes = document.activeElement === area;
    ponteiro = true;
    alvo = destino(event);
    toque = event.pointerType === "touch" ? {i: alvo, t: performance.now()} : null;
    pintar();
  });
  area.addEventListener("pointercancel", () => { alvo = null; pintar(); });
  area.addEventListener("click", event => {
    const i = event.detail > 1 ? destino(event) : alvo ?? destino(event);
    ponteiro = false;
    toque = null;
    alvo = null;
    if (event.detail === 1 && area.selectionStart !== area.selectionEnd) { pintar(); return; }
    irPara(i);
  });
  $("caixa").addEventListener("mousedown", event => {
    if (event.target !== $("caixa")) return;
    event.preventDefault();
    area.focus();
    irPara(continuar());
  });
  // Foco pelo teclado (Tab) retoma de onde parou.
  area.addEventListener("focus", () => {
    if (!ponteiro && retomar) irPara(continuar());
    ponteiro = false;
    pintar();
  });
  area.addEventListener("blur", () => {
    retomar = document.activeElement !== area;  // trocar de janela mantém o cursor
    flush();
    toque = null;
    alvo = null;
    pintar();
  });
  if (matchMedia("(hover: hover)").matches) {
    area.addEventListener("pointermove", event => {
      const i = celulaEm(event);
      if (i !== hover) { hover = i; pintar(); }
    });
    area.addEventListener("pointerleave", () => { hover = null; pintar(); });
  }

  // Setas andam por questão e por linha da grade, sem depender de como o
  // navegador quebra o texto. Com Shift, a seleção nativa estende.
  area.addEventListener("keydown", event => {
    alvo = null;
    if (event.isComposing || event.keyCode === 229) return;
    const {key, shiftKey, altKey} = event;
    const ctrl = event.ctrlKey || event.metaKey;
    if (key === "Escape") { area.blur(); return; }
    if (key === "Enter") { event.preventDefault(); area.blur(); return; }
    if (shiftKey || altKey) return;
    const [ini, fim] = [area.selectionStart, area.selectionEnd];
    const n = geo.porLinha || TOTAL, c = Math.min(ini, TOTAL - 1);
    const linha = c - (c % n);
    let para = null;
    if (key === "ArrowLeft") para = ctrl ? linha : fim > ini ? ini : Math.max(ini - 1, 0);
    else if (key === "ArrowRight") para = ctrl ? Math.min(linha + n, TOTAL) - 1 : fim > ini ? fim - 1 : Math.min(ini + 1, TOTAL - 1);
    else if (key === "ArrowUp") para = c - n >= 0 ? c - n : c;
    else if (key === "ArrowDown") para = c + n < TOTAL ? c + n : c;
    else if (key === "Home") para = ctrl ? 0 : linha;
    else if (key === "End") para = ctrl ? TOTAL - 1 : Math.min(linha + n, TOTAL) - 1;
    if (para === null) return;
    event.preventDefault();
    irPara(para);
  });
  for (const tipo of ["keyup", "select", "selectionchange"]) area.addEventListener(tipo, pintar);
  // O toque longo seleciona a "palavra", que pode ser a folha inteira: fica só
  // a questão tocada, para colar ou trocar ali.
  document.addEventListener("selectionchange", () => {
    if (toque && toque.i !== null && area.selectionEnd - area.selectionStart > 1
        && performance.now() - toque.t < 2000) {
      const {i} = toque;
      toque = null;
      area.setSelectionRange(i, i + 1);
    }
    pintar();
  });
  // Garante que nenhuma rolagem interna desalinhe o texto das células.
  area.addEventListener("scroll", () => { area.scrollTop = 0; area.scrollLeft = 0; });
  $("folha").addEventListener("scroll", event => { event.target.scrollTop = 0; event.target.scrollLeft = 0; });
  new ResizeObserver(() => { layout(); resizeFrame(); }).observe(document.body);
  document.fonts.ready.then(() => layout(true));
  document.fonts.addEventListener("loadingdone", () => layout(true));
}

function onRender(event) {
  const theme = event.detail.theme;
  if (theme) {
    for (const [css, name] of Object.entries({
      "primary-color": "primaryColor", "background-color": "backgroundColor",
      "secondary-background-color": "secondaryBackgroundColor", "text-color": "textColor",
    })) document.documentElement.style.setProperty(`--${css}`, theme[name]);
  }
  const args = event.detail.args;
  inicio = Number(args.inicio) || 1;
  // Python echoes values asynchronously. Do not replace drafts or selection.
  if (!initialized) {
    iniciar(args);
    initialized = true;
    layout(true);
  }
  pintar();
  resizeFrame();
}
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();
