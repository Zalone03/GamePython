import { useCallback, useEffect, useRef, useState } from "react";
import { JOGOS } from "../jogos/catalogo";
import { entregarLinha, pararJogo, rodarJogo, teclaNoPygame } from "../python/motor";
import { novoId, proximoQuadro } from "../util/utilidades";
import { useInicializacao } from "./useInicializacao";
import { useTeclado } from "./useTeclado";

// ===========
// Barra de status
// ===========

// Texto da barra de status para cada modo
function textoDoStatus(modo, partida) {
  if (modo === "boot") return "INICIALIZANDO...";
  if (modo === "offline") return "ERRO";
  if (modo === "menu") return "SELECIONE UM JOGO";
  if (modo === "jogo") return `JOGANDO: ${partida?.jogo.nome ?? ""}`;
  return "FIM DE JOGO";
}

// ===========
// Portátil
// ===========

// Toda a lógica do portátil: modos boot -> menu -> jogo -> fim (ou offline)
export function useArcade() {
  // ===========
  // Estado
  // ===========

  // Modo atual da tela
  const [modo, setModo] = useState("boot");

  // Jogo marcado no menu
  const [selecionado, setSelecionado] = useState(0);

  // Partida em andamento: { id, jogo }
  const [partida, setPartida] = useState(null);

  // Pedaços de texto que o jogo imprimiu: [{ texto, classe }]
  const [saida, setSaida] = useState([]);

  // O que o jogador está digitando agora
  const [digitado, setDigitado] = useState("");

  // Id da partida atual (ignora saída de partidas antigas)
  const idAtual = useRef(null);

  // Promessa do jogo que está rodando agora
  const execucao = useRef(Promise.resolve());

  // ===========
  // Abertura
  // ===========

  const abertura = useInicializacao(JOGOS.length);

  // Sai da abertura para o menu (ou para a tela de erro)
  useEffect(() => {
    if (abertura.estado === "pronto") setModo("menu");
    if (abertura.estado === "erro") setModo("offline");
  }, [abertura.estado]);

  // ===========
  // Ações
  // ===========

  // Acrescenta texto na tela da partida
  const escrever = useCallback((texto, classe = "") => {
    setSaida((s) => [...s, { texto, classe }]);
  }, []);

  // Marca um jogo no menu (dá a volta no começo/fim da lista)
  function selecionar(indice) {
    const total = JOGOS.length;
    setSelecionado(((indice % total) + total) % total);
  }

  // Volta para o menu limpando a partida
  function irParaMenu() {
    idAtual.current = null;
    setPartida(null);
    setSaida([]);
    setDigitado("");
    setModo("menu");
  }

  // Começa um jogo e espera ele terminar
  async function iniciar(indice = selecionado) {
    const jogo = JOGOS[indice];
    if (!jogo) return;
    const id = novoId();
    idAtual.current = id;
    setSelecionado(indice);
    setPartida({ id, jogo });
    setSaida([]);
    setDigitado("");
    setModo("jogo");

    // Espera o jogo anterior terminar de fechar
    await execucao.current;
    if (idAtual.current !== id) return;

    // Só escreve se ainda for esta partida
    const escreverNaPartida = (texto, classe) => {
      if (idAtual.current === id) escrever(texto.replace(/\r\n?/g, "\n"), classe);
    };

    // Roda o jogo depois que a tela (e o canvas) já apareceu
    async function rodar() {
      await proximoQuadro();
      try {
        await rodarJogo(jogo, { escrever: escreverNaPartida });
      } catch (erro) {
        escreverNaPartida(`\nErro: ${erro.message}\n`, "erro");
      }
    }

    execucao.current = rodar();
    await execucao.current;

    // O programa .py terminou: agora quem decide é o jogador
    if (idAtual.current === id) {
      idAtual.current = null;
      setModo("fim");
      escrever("\n\n[ FIM DE JOGO ]  ENTER joga de novo  ·  ESC volta ao menu\n", "sistema");
    }
  }

  // Manda o que foi digitado para o input() do jogo
  function enviar() {
    const texto = digitado;
    setDigitado("");
    // O Python não ecoa o que foi digitado, então mostramos aqui
    escrever(texto + "\n", "eco");
    entregarLinha(texto);
  }

  // Interrompe o jogo e volta ao menu
  function sair() {
    pararJogo();
    irParaMenu();
  }

  // ===========
  // Teclado
  // ===========

  // Menu: setas escolhem, números pulam direto, ENTER joga
  function teclaNoMenu(e) {
    const numero = Number(e.key);
    if (e.key === "ArrowUp") selecionar(selecionado - 1);
    else if (e.key === "ArrowDown") selecionar(selecionado + 1);
    else if (e.key === "Enter") iniciar();
    else if (numero >= 1 && numero <= JOGOS.length) selecionar(numero - 1);
    else return;
    e.preventDefault();
  }

  // Jogo: ESC sai; o resto é digitado no campo invisível (ver JogoTexto)
  function teclaNoJogo(e) {
    if (e.key === "Escape") {
      e.preventDefault();
      return sair();
    }
    const entrada = document.querySelector(".entrada-oculta");
    // Só age se o campo de digitação perdeu o foco
    if (partida?.jogo.tipo !== "texto" || !entrada || e.target === entrada) return;
    if (e.key === "Enter") {
      e.preventDefault();
      enviar();
    } else {
      entrada.focus({ preventScroll: true });
    }
  }

  // Fim: ENTER joga de novo, ESC volta ao menu
  function teclaNoFim(e) {
    // Ignora o ENTER segurado da última jogada
    if (e.repeat) return;
    if (e.key === "Enter") iniciar(selecionado);
    else if (e.key === "Escape") irParaMenu();
    else return;
    e.preventDefault();
  }

  // Decide o que cada tecla faz em cada modo
  function tratarTecla(e) {
    // Atalhos do navegador (Ctrl+C, etc.) passam direto
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (modo === "boot") return abertura.pular();
    if (modo === "menu") return teclaNoMenu(e);
    if (modo === "jogo") return teclaNoJogo(e);
    if (modo === "fim") return teclaNoFim(e);
  }

  useTeclado(tratarTecla);

  // ===========
  // Botões do celular
  // ===========

  // Cruz direcional e A/B: viram as mesmas teclas do teclado
  function pressionar(tecla) {
    const tipo = modo === "jogo" ? partida?.jogo.tipo : null;
    // No Snake, as setas vão direto para o jogo
    if (tipo === "pygame" && tecla.startsWith("Arrow")) return teclaNoPygame(tecla);
    // Num jogo de texto, o A envia o que foi digitado
    if (tipo === "texto" && tecla === "Enter") return enviar();
    if (tipo && tecla === "Enter") return;
    tratarTecla({ key: tecla, preventDefault() {} });
  }

  return {
    modo,
    status: textoDoStatus(modo, partida),
    linhasBoot: abertura.linhas,
    jogos: JOGOS,
    selecionado,
    partida,
    saida,
    digitado,
    selecionar,
    iniciar,
    enviar,
    setDigitado,
    pressionar,
  };
}
