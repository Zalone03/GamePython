import { useEffect, useRef } from "react";

// ===========
// Jogo de texto
// ===========

// Mostra o que o jogo imprime e captura o que o jogador digita
export default function JogoTexto({ saida, digitado, rodando, aoDigitar, aoEnviar }) {
  const entradaRef = useRef(null);

  // O campo invisível recebe o foco assim que o jogo começa
  useEffect(() => {
    if (rodando) entradaRef.current?.focus({ preventScroll: true });
  }, [rodando]);

  // ENTER no campo envia a linha para o jogo
  function aoTeclar(e) {
    if (e.key !== "Enter") return;
    e.preventDefault();
    aoEnviar();
  }

  return (
    <>
      {rodando && <div className="dica so-celular">(toque na tela para digitar)</div>}
      <div>&nbsp;</div>

      <div>
        {saida.map((pedaco, i) => (
          <span key={i} className={pedaco.classe}>
            {pedaco.texto}
          </span>
        ))}
        {rodando && (
          <>
            <span className="eco">{digitado}</span>
            <span className="cursor" />
          </>
        )}
      </div>

      {rodando && (
        <input
          ref={entradaRef}
          className="entrada-oculta"
          value={digitado}
          onChange={(e) => aoDigitar(e.target.value)}
          onKeyDown={aoTeclar}
          autoComplete="off"
          autoCapitalize="off"
          spellCheck={false}
          aria-label="Entrada do jogo"
        />
      )}
    </>
  );
}
