import { useLayoutEffect, useRef } from "react";
import Relogio from "./Relogio";
import Menu from "./Menu";
import Partida from "./Partida";

// ===========
// Tela
// ===========

// Moldura escura com o LCD: barra de status em cima e terminal embaixo
export default function Tela({ arcade }) {
  const {
    modo, status, linhasBoot, jogos, selecionado, partida, saida, digitado,
    selecionar, iniciar, enviar, setDigitado,
  } = arcade;
  const terminalRef = useRef(null);

  // Jogo pygame ocupa o terminal inteiro com o canvas
  const ehPygame = modo === "jogo" && partida?.jogo.tipo === "pygame";

  // Rola o terminal para o fim quando aparece texto novo (no menu, volta para o topo)
  useLayoutEffect(() => {
    const terminal = terminalRef.current;
    if (terminal) terminal.scrollTop = modo === "menu" ? 0 : terminal.scrollHeight;
  }, [modo, linhasBoot, saida, digitado]);

  // Tocar na tela devolve o foco ao campo de digitação (no celular, abre o teclado)
  function focarEntrada() {
    terminalRef.current?.querySelector(".entrada-oculta")?.focus({ preventScroll: true });
  }

  // Clicar num jogo já marcado começa a partida
  function clicarNoJogo(indice) {
    if (indice === selecionado) iniciar(indice);
    else selecionar(indice);
  }

  return (
    <section className="moldura">
      <div className="rotulo-moldura">GAMEPYTHON</div>
      <div className="tela">
        <div className="barra-status">
          <span>{status}</span>
          <span>
            P1 &middot; <Relogio />
          </span>
        </div>

        <div
          ref={terminalRef}
          className={ehPygame ? "terminal terminal-palco" : "terminal"}
          tabIndex={0}
          aria-live="polite"
          onClick={focarEntrada}
        >
          {(modo === "boot" || modo === "offline") &&
            linhasBoot.map((linha, i) => (
              <div key={i} className={linha.classe}>
                {linha.texto}
              </div>
            ))}

          {modo === "menu" && <Menu jogos={jogos} selecionado={selecionado} aoClicar={clicarNoJogo} />}

          {(modo === "jogo" || modo === "fim") && partida && (
            <Partida
              jogo={partida.jogo}
              saida={saida}
              digitado={digitado}
              rodando={modo === "jogo"}
              aoDigitar={setDigitado}
              aoEnviar={enviar}
            />
          )}
        </div>
      </div>
    </section>
  );
}
