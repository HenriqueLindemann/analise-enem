// Adapted from streamlit-keyup 0.3.0 (Zachary Blackwood); see LICENSE.
// A native textarea keeps caret, copy/paste, undo and mobile keyboards. Every
// glyph gets the same width, so a layer behind it numbers each answer.
const TOTAL = 45, BLOCO = 5, VALIDAS = "ABCDE.*";
// Questão pulada (ainda sem resposta): invisível e com a largura de uma letra.
// Fora do campo vira "_", que o Python conta como resposta faltando.
const FALTA = "\u00a0";
const paraFora = v => v.replaceAll(FALTA, "_");
const paraDentro = v => v.toUpperCase().replaceAll("_", FALTA);
const NUM = 15, LIN = 28, ENTRE = 8;   // px: números, letras, entre linhas
const PASSO = NUM + LIN + ENTRE;
const MARGEM = 2;                      // px: folga das faixas na primeira e na última linha
const CELULA_MAX = 30;
let initialized = false;
let timer;
let lastSent;
let frameHeight = 0;
let inicio = 1;
let geo = {};
let sobrescrever = false; // após selecionar uma resposta, digitar troca em vez de inserir
let vazia = null;         // questão vazia escolhida além da última resposta
let focadoAntes = false;
let hover = null;
let colada = new Set();
let composicao = null;    // campo antes da composição do teclado (Android)
let aviso = "", avisoTimer;
let flush = () => {};
let agendar = () => {};

const $ = id => document.getElementById(id);
const ta = () => $("input_box");

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
function layout(forcar = false) {
  const area = ta(), folha = $("folha");
  const disponivel = $("caixa").clientWidth - 20;  // padding da caixa
  if (!forcar && disponivel === geo.disponivel) return;
  const ch = larguraCaractere(area);
  const minimo = Math.max(ch + 7, 20);
  const porLinha = [45, 25, 15, 10].find(n => disponivel / n >= minimo) || 10;
  const cel = Math.min(disponivel / porLinha, CELULA_MAX);
  const linhas = Math.ceil(TOTAL / porLinha);
  const espaco = cel - ch;
  geo = {cel, porLinha, disponivel};
  Object.assign(area.style, {
    letterSpacing: `${espaco}px`, lineHeight: `${PASSO}px`,
    // Centro da linha de texto = centro da linha das letras.
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
  const valor = area.value;
  const n = valor.length;
  const foco = document.activeElement === area;
  const [ini, fim] = [area.selectionStart, area.selectionEnd];
  let troca = null, proxima = null, insercao = null;
  if (foco && vazia !== null) troca = vazia;
  else if (foco && fim - ini === 1) troca = ini;
  else if (foco && ini === fim && ini < n && (n === TOTAL || sobrescrever)) troca = ini;
  else if (foco && ini === fim && ini === n && n < TOTAL) proxima = ini;
  else if (foco && ini === fim && ini < n) insercao = ini;
  const ativo = troca ?? proxima ?? insercao;
  document.body.classList.toggle("virtual", foco && vazia !== null);
  let invalidos = 0, feitas = 0;
  $("camada").querySelectorAll(".cel").forEach((el, i) => {
    const c = valor[i];
    const falta = c === undefined || c === FALTA;
    const invalida = !falta && !VALIDAS.includes(c);
    invalidos += invalida;
    feitas += !falta;
    el.className = "cel"
      + (falta ? " cel--vazia" : "")
      + (invalida ? " cel--invalida" : "")
      + (i === troca ? " cel--troca" : "")
      + (i === proxima ? " cel--proxima" : "")
      + (foco && fim - ini > 1 && i >= ini && i < fim ? " cel--sel" : "")
      + (colada.has(i) ? " cel--colada" : "");
  });
  $("camada").querySelectorAll(".num").forEach((el, i) => {
    const texto = String(inicio + i);
    if (el.textContent !== texto) el.textContent = texto;
    el.className = "num"
      + (i % BLOCO === 0 ? " num--bloco" : "")
      + (i === hover ? " num--hover" : "")
      + (i === ativo ? " num--ativo" : "");
  });
  const contador = $("contador");
  contador.className = invalidos ? "invalido" : feitas === TOTAL ? "completo" : "";
  contador.textContent = invalidos
    ? `${invalidos} ${invalidos > 1 ? "caracteres inválidos" : "caractere inválido"}`
    : feitas === 0 ? `0/${TOTAL} respostas`
    : feitas === TOTAL ? `${TOTAL}/${TOTAL} respostas · completo`
    : `${feitas}/${TOTAL} respostas · faltam ${TOTAL - feitas}`;
  const posicao = $("posicao");
  posicao.className = aviso ? "aviso" : "";
  posicao.textContent = aviso
    || (troca !== null && troca < n && valor[troca] !== FALTA ? `Questão ${inicio + troca} · substituir`
      : ativo !== null ? `Questão ${inicio + ativo}`
      : foco && fim - ini > 1 ? `Questões ${inicio + ini}–${inicio + fim - 1}`
      : "");
}

// Troca [s, f) por texto; execCommand preserva o desfazer nativo.
function editar(s, f, texto) {
  const area = ta();
  area.setSelectionRange(s, f);
  let ok = false;
  try { ok = document.execCommand("insertText", false, texto); } catch (e) { ok = false; }
  if (!ok) area.setRangeText(texto, s, f, "end");
  if (aviso) avisar("");
  pintar();
  agendar();
}

// Intervalo a substituir por k letras: selecionar ou completar a área faz trocar.
function intervalo(k) {
  const area = ta(), n = area.value.length;
  let [s, f] = [area.selectionStart, area.selectionEnd];
  if (f - s <= 1 && s < n && (f - s === 1 || n === TOTAL || sobrescrever)) f = Math.min(s + k, n);
  return [s, f];
}

function destacar(de, ate) {
  colada = new Set(Array.from({length: Math.max(0, ate - de)}, (_, k) => de + k));
  setTimeout(() => { colada = new Set(); pintar(); }, 650);
}

// Questões puladas até a vazia escolhida ficam sem resposta, não em branco.
function saltar() {
  const n = ta().value.length;
  const salto = vazia === null ? "" : FALTA.repeat(vazia - n);
  vazia = null;
  return salto;
}

// Digitar: minúscula vira maiúscula e espaço vira ponto (em branco).
function digitar(dado) {
  const area = ta();
  const letras = dado.toUpperCase().replace(/ /g, ".");
  if ([...letras].some(c => !VALIDAS.includes(c))) {
    avisar(`“${dado}” não é alternativa · use A a E ou ponto`);
    return;
  }
  const n = area.value.length;
  if (vazia !== null) {
    const salto = saltar();
    editar(n, n, (salto + letras).slice(0, TOTAL - n));
    return;
  }
  const [s, f] = intervalo(letras.length);
  const cabe = TOTAL - (n - (f - s));
  if (cabe <= 0) { avisar("Área completa · selecione uma questão para trocar"); return; }
  editar(s, f, letras.slice(0, cabe));
  if (area.selectionStart >= area.value.length) sobrescrever = false;
}

// Colar: aceita 45 letras seguidas, com espaços, ou numeradas ("46-A, 47-B").
function colar(texto) {
  const area = ta(), v = area.value;
  const pares = [...texto.matchAll(/(\d{1,3})\s*[-–—.:)=]?\s*([A-Ea-e*])(?![A-Za-z])/g)];
  if (pares.length >= 3) {
    const lista = v.split("");
    let usados = 0;
    for (const [, numero, letra] of pares) {
      const q = Number(numero);
      const i = q >= inicio && q < inicio + TOTAL ? q - inicio : q >= 1 && q <= TOTAL ? q - 1 : -1;
      if (i < 0) continue;
      while (lista.length < i) lista.push(FALTA);
      lista[i] = letra.toUpperCase();
      usados += 1;
    }
    if (usados) {
      vazia = null;
      editar(0, v.length, lista.join("").slice(0, TOTAL));
      destacar(0, area.value.length);
      avisar(`${usados} respostas coladas pelo número da questão`);
      return;
    }
  }
  const limpo = texto.replaceAll(FALTA, "_").toUpperCase().replace(/[\s,;|]+/g, "");
  const ignorados = [...new Set([...limpo].filter(c => !VALIDAS.includes(c) && c !== "_"))];
  const letras = paraDentro([...limpo].filter(c => VALIDAS.includes(c) || c === "_").join(""));
  if (!letras) { avisar("Nada para colar · use letras de A a E"); return; }
  const n = v.length;
  let [s, f] = letras.length >= TOTAL ? [0, n] : intervalo(letras.length);
  const salto = letras.length >= TOTAL ? (vazia = null, "") : saltar();
  if (salto) [s, f] = [n, n];
  const cabe = TOTAL - (n - (f - s)) - salto.length;
  const entra = letras.slice(0, Math.max(0, cabe));
  editar(s, f, salto + entra);
  destacar(s + salto.length, s + salto.length + entra.length);
  if (ignorados.length) avisar(`Ignorado ao colar: ${ignorados.join(" ")}`);
  else if (entra.length < letras.length) avisar(`Só ${entra.length} de ${letras.length} letras cabiam`);
}

// Texto que chegou direto ao campo: maiúsculas, espaço vira ponto e, se
// passar de 45, as letras seguintes são trocadas.
function normalizar() {
  const area = ta();
  let v = area.value.toUpperCase().replace(/[^\S\u00a0]/g, ".").replace(/\u00a0+$/, "");
  let [s, f] = [area.selectionStart, area.selectionEnd];
  if (v.length > TOTAL) {
    const sobra = v.length - TOTAL;
    v = s < v.length ? v.slice(0, s) + v.slice(s + sobra) : v.slice(0, TOTAL);
    s = f = Math.min(s, TOTAL);
  }
  if (v === area.value) return;
  area.value = v;
  area.setSelectionRange(s, f);
}

// Na composição o teclado escreve direto no campo, sem passar por digitar().
// Ao fim dela, o trecho novo é refeito como digitação: troca a resposta
// escolhida, preenche a questão vazia escolhida e recusa letras inválidas.
function reconciliar() {
  const antes = composicao, area = ta(), depois = area.value;
  composicao = null;
  if (!antes || depois === antes.valor) { normalizar(); return; }
  const v = antes.valor;
  let p = 0, s = 0;
  while (p < v.length && p < depois.length && v[p] === depois[p]) p++;
  while (s < v.length - p && s < depois.length - p && v[v.length - 1 - s] === depois[depois.length - 1 - s]) s++;
  const removido = v.slice(p, v.length - s), novo = depois.slice(p, depois.length - s);
  // Fora de inserir no cursor ou trocar a seleção (ex.: apagar), só normaliza.
  if (!novo || (removido && removido !== v.slice(antes.ini, antes.fim))) { normalizar(); return; }
  area.value = v;
  area.setSelectionRange(antes.ini, antes.fim);
  ({vazia, sobrescrever} = antes);
  const letras = [...novo.toUpperCase().replace(/[^\S\u00a0]/g, ".")];
  const validas = letras.filter(c => VALIDAS.includes(c)).join("");
  if (validas) digitar(validas);
  const recusadas = [...novo].filter(c => !/\s/.test(c) && !VALIDAS.includes(c.toUpperCase())).join("");
  if (recusadas) avisar(`“${recusadas}” não é alternativa · use A a E ou ponto`);
}

function iniciar(args) {
  const {label, value, debounce} = args;
  const area = ta();
  $("label").textContent = label;
  area.value = paraDentro(value || "").slice(0, TOTAL).replace(/\u00a0+$/, "");
  lastSent = paraFora(area.value);
  herdarFontes();
  construir();
  flush = () => {
    clearTimeout(timer);
    if (paraFora(area.value) !== lastSent) {
      lastSent = paraFora(area.value);
      Streamlit.setComponentValue(lastSent);
    }
  };
  agendar = () => { clearTimeout(timer); timer = setTimeout(flush, debounce); };

  area.addEventListener("beforeinput", event => {
    if (event.isComposing || event.inputType === "insertCompositionText") return;
    if (event.inputType === "insertText" && event.data) {
      event.preventDefault();
      digitar(event.data);
    } else if (event.inputType === "insertLineBreak" || event.inputType === "insertParagraph") {
      event.preventDefault();
      flush();
    } else if (event.inputType.startsWith("delete")) {
      if (vazia !== null) {  // só desfaz a escolha da questão vazia
        event.preventDefault();
        vazia = null;
        pintar();
        return;
      }
      // Apagar desloca as respostas seguintes; a próxima letra volta a inserir.
      sobrescrever = false;
    }
  });
  // Copiar leva "_" no lugar das questões puladas.
  for (const tipo of ["copy", "cut"]) area.addEventListener(tipo, event => {
    const [s, f] = [area.selectionStart, area.selectionEnd];
    if (s === f || !event.clipboardData) return;
    event.preventDefault();
    event.clipboardData.setData("text/plain", paraFora(area.value.slice(s, f)));
    if (tipo === "cut") editar(s, f, "");
  });
  area.addEventListener("paste", event => {
    event.preventDefault();
    colar(event.clipboardData ? event.clipboardData.getData("text") : "");
  });
  area.addEventListener("input", event => {
    if (!event.isComposing) normalizar();
    pintar();
    agendar();
  });
  area.addEventListener("compositionstart", () => {
    composicao = {valor: area.value, ini: area.selectionStart, fim: area.selectionEnd, vazia, sobrescrever};
  });
  area.addEventListener("compositionend", () => { reconciliar(); pintar(); agendar(); });
  area.addEventListener("pointerdown", () => { focadoAntes = document.activeElement === area; });
  // Selecionar uma resposta permite trocá-la; uma questão vazia adiante
  // também pode ser escolhida, menos no primeiro toque num campo vazio.
  area.addEventListener("click", event => {
    if (area.selectionStart !== area.selectionEnd) return;
    const i = celulaEm(event), n = area.value.length;
    vazia = null;
    if (i !== null && i < n) {
      area.setSelectionRange(i, i + 1);
      sobrescrever = true;
    } else {
      area.setSelectionRange(n, n);
      sobrescrever = false;
      if (i !== null && i > n && (n > 0 || focadoAntes)) vazia = i;
    }
    if (aviso) avisar("");
    pintar();
  });
  $("caixa").addEventListener("mousedown", event => {
    if (event.target !== $("caixa")) return;
    event.preventDefault();
    area.focus();
    area.setSelectionRange(area.value.length, area.value.length);
    pintar();
  });
  if (matchMedia("(hover: hover)").matches) {
    area.addEventListener("pointermove", event => {
      const i = celulaEm(event);
      if (i !== hover) { hover = i; pintar(); }
    });
    area.addEventListener("pointerleave", () => { hover = null; pintar(); });
  }
  area.addEventListener("blur", () => { flush(); sobrescrever = false; vazia = null; pintar(); });
  area.addEventListener("focus", pintar);
  area.addEventListener("keydown", event => {
    if (event.key === "Escape") area.blur();
    if (event.key.startsWith("Arrow") || event.key === "Home" || event.key === "End") vazia = null;
  });
  for (const tipo of ["keyup", "select", "selectionchange"]) area.addEventListener(tipo, pintar);
  document.addEventListener("selectionchange", pintar);
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
