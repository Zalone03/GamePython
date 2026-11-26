import { telaPygame } from "../python/motor";

// ===========
// Jogo pygame
// ===========

// Coloca o canvas do pygame dentro da tela (uma vez só)
function encaixarCanvas(palco) {
  if (palco && !palco.contains(telaPygame)) palco.append(telaPygame);
}

// Canvas onde o pygame desenha + a última mensagem do jogo e os controles
export default function JogoPygame({ jogo, saida }) {
  const texto = saida.map((pedaco) => pedaco.texto).join("");
  const ultimaLinha = texto.trimEnd().split("\n").at(-1) || "Iniciando...";

  return (
    <>
      <div className="dica linha-unica">{ultimaLinha}</div>
      <div className="palco" ref={encaixarCanvas} />
      <div className="dica linha-unica">{jogo.controles}</div>
    </>
  );
}
