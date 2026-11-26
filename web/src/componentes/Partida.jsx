import JogoTexto from "./JogoTexto";
import JogoPygame from "./JogoPygame";

// ===========
// Partida
// ===========

// Linha de comando + o jogo (texto no terminal ou pygame no canvas)
export default function Partida({ jogo, saida, digitado, rodando, aoDigitar, aoEnviar }) {
  // Quando o Snake termina, mostra o texto (mensagens e possíveis erros)
  const mostrarCanvas = jogo.tipo === "pygame" && rodando;

  return (
    <>
      <div className="sistema">C:\GAMEPYTHON&gt; python {jogo.arquivo}</div>
      {mostrarCanvas ? (
        <JogoPygame jogo={jogo} saida={saida} />
      ) : (
        <JogoTexto saida={saida} digitado={digitado} rodando={rodando} aoDigitar={aoDigitar} aoEnviar={aoEnviar} />
      )}
    </>
  );
}
