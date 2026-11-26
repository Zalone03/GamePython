import { PRELUDIO, PRELUDIO_PYGAME } from "./preludio";
import { proximoQuadro } from "../util/utilidades";

// ===========
// Configuração
// ===========

// Versão do Pyodide (Python 3.14 compilado para WebAssembly)
const VERSAO_PYODIDE = "314.0.8";

// Endereço de onde o Python é baixado na primeira vez
const CDN = `https://cdn.jsdelivr.net/pyodide/v${VERSAO_PYODIDE}/full/`;

// Título original da aba (o pygame troca ao abrir a janela)
const TITULO = document.title;

// ===========
// Canvas do pygame
// ===========

// Canvas onde o pygame desenha, colocado dentro da tela do portátil
export const telaPygame = document.createElement("canvas");
telaPygame.id = "canvas";
telaPygame.tabIndex = 0;

// ===========
// Ponte Python <-> página
// ===========

// Função que recebe o texto que o jogo imprime
let aoEscrever = () => {};

// Linhas digitadas antes de o jogo pedir input()
let filaDeLinhas = [];

// resolve() do input() que está esperando o jogador
let linhaPendente = null;

// Vira true quando o jogador aperta ESC
let parado = false;

// Funções que o Python enxerga como o módulo "ponte"
const ponte = {
  lerLinha: () =>
    new Promise((resolve) => {
      if (filaDeLinhas.length) resolve(filaDeLinhas.shift());
      else linhaPendente = resolve;
    }),
  esperar: (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  proximoQuadro,
  parado: () => parado,
};

// ===========
// Carregamento
// ===========

// Promessa do Pyodide carregado (carrega uma vez só)
let promessaPyodide = null;

// Diz se o pygame já foi baixado e configurado
let pygamePronto = false;

// Pastas de jogos já gravadas no disco virtual do Python
const pastasInstaladas = new Set();

// Onde as pastas dos jogos ficam no disco virtual
const RAIZ_DOS_JOGOS = "/jogos";

// Diz se o navegador consegue pausar o Python (recurso JSPI do Chrome/Edge)
export function suportaPython() {
  return typeof WebAssembly !== "undefined" && typeof WebAssembly.Suspending === "function";
}

// Cria um escritor que manda a saída do Python para a tela
function criarEscritor(classe) {
  const decodificador = new TextDecoder();
  return {
    // isatty faz o Python mandar a saída linha a linha (e não em blocos)
    isatty: true,
    write: (buffer) => {
      aoEscrever(decodificador.decode(buffer, { stream: true }), classe);
      return buffer.length;
    },
  };
}

// Baixa e prepara o Python
async function iniciarPyodide() {
  const endereco = `${CDN}pyodide.mjs`;
  const { loadPyodide } = await import(endereco);
  const py = await loadPyodide({ indexURL: CDN });
  py.setStdout(criarEscritor(""));
  py.setStderr(criarEscritor("erro"));
  py.registerJsModule("ponte", ponte);
  py.runPython(PRELUDIO);
  return py;
}

// Devolve o Python pronto (se falhar, deixa tentar de novo)
export function carregarPython() {
  if (!promessaPyodide) {
    promessaPyodide = iniciarPyodide();
    promessaPyodide.catch(() => {
      promessaPyodide = null;
    });
  }
  return promessaPyodide;
}

// Baixa o pygame e liga ele ao canvas (só na primeira vez)
async function prepararPygame(py, escrever) {
  if (pygamePronto) return;
  escrever("Carregando pygame...\n", "sistema");
  await py.loadPackage("pygame-ce", { messageCallback: () => {} });
  py.canvas.setCanvas2D(telaPygame);
  py.runPython(PRELUDIO_PYGAME);
  pygamePronto = true;
}

// Baixa um arquivo e devolve os bytes
async function baixar(url) {
  const resposta = await fetch(url);
  return new Uint8Array(await resposta.arrayBuffer());
}

// Grava um arquivo no disco virtual, criando as pastas do caminho
function gravar(py, caminho, dados) {
  py.FS.mkdirTree(caminho.slice(0, caminho.lastIndexOf("/")));
  py.FS.writeFile(caminho, dados);
}

// Aplica os "ajustes" do catálogo num arquivo (só na cópia do navegador; o original não muda)
function ajustar(jogo, relativo, dados) {
  const ajustes = (jogo.ajustes ?? []).filter((ajuste) => ajuste.arquivo === relativo);
  if (!ajustes.length) return dados;
  let texto = new TextDecoder().decode(dados);
  for (const { de, para } of ajustes) {
    // Avisa no console se o arquivo mudou e o trecho não existe mais
    if (!texto.includes(de)) console.warn(`Ajuste não encontrado em ${relativo}: ${de}`);
    texto = texto.replace(de, para);
  }
  return new TextEncoder().encode(texto);
}

// Baixa todos os arquivos de um jogo com pasta própria (só na primeira vez)
async function instalarPasta(py, jogo, escrever) {
  if (pastasInstaladas.has(jogo.pasta)) return;
  // Caminho relativo à pasta do jogo, em ordem alfabética (o jogo lê as animações nessa ordem)
  const arquivos = Object.entries(jogo.arquivos)
    .map(([caminho, url]) => [caminho.split(`/${jogo.pasta}/`)[1], url])
    .sort(([a], [b]) => (a < b ? -1 : 1));
  escrever(`Carregando ${arquivos.length} arquivos do jogo...\n`, "sistema");
  const baixados = await Promise.all(arquivos.map(([, url]) => baixar(url)));
  arquivos.forEach(([relativo], i) => {
    gravar(py, `${RAIZ_DOS_JOGOS}/${jogo.pasta}/${relativo}`, ajustar(jogo, relativo, baixados[i]));
  });
  pastasInstaladas.add(jogo.pasta);
}

// ===========
// Partida
// ===========

// Roda um jogo .py até ele terminar (ou o jogador apertar ESC)
export async function rodarJogo(jogo, { escrever }) {
  const py = await carregarPython();
  aoEscrever = escrever;
  filaDeLinhas = [];
  linhaPendente = null;
  parado = false;
  try {
    if (jogo.pasta) await instalarPasta(py, jogo, escrever);
    if (jogo.tipo === "pygame") {
      await prepararPygame(py, escrever);
      // musica: false no catálogo deixa o jogo sem música de fundo
      py.runPython(`_permitir_musica(${jogo.musica === false ? "False" : "True"})`);
      telaPygame.focus({ preventScroll: true });
    }
    if (parado) return;
    py.globals.set("_arquivo", jogo.arquivo);
    py.globals.set("_codigo", jogo.codigo ?? null);
    py.globals.set("_pasta", jogo.pasta ? `${RAIZ_DOS_JOGOS}/${jogo.pasta}` : null);
    await py.runPythonAsync("_executar(_arquivo, _codigo, _pasta)");
  } finally {
    aoEscrever = () => {};
    linhaPendente = null;
    document.title = TITULO;
  }
}

// Envia uma linha digitada para o input() do jogo
export function entregarLinha(texto) {
  if (!linhaPendente) return filaDeLinhas.push(texto);
  const resolver = linhaPendente;
  linhaPendente = null;
  resolver(texto);
}

// Interrompe o jogo atual (ESC)
export function pararJogo() {
  parado = true;
  if (linhaPendente) entregarLinha("");
}

// Simula uma tecla no jogo pygame (usado pela cruz direcional do celular)
export function teclaNoPygame(codigo) {
  for (const tipo of ["keydown", "keyup"]) {
    telaPygame.dispatchEvent(new KeyboardEvent(tipo, { key: codigo, code: codigo, bubbles: true }));
  }
}
