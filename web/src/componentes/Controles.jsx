// ===========
// Controles do celular
// ===========

// Impede o botão de roubar o foco (o teclado do celular não fecha)
const manterFoco = (e) => e.preventDefault();

// Um botão que "aperta" uma tecla
function Botao({ tecla, classe, rotulo, aoApertar }) {
  return (
    <button
      type="button"
      className={classe}
      aria-label={rotulo}
      onMouseDown={manterFoco}
      onClick={() => aoApertar(tecla)}
    />
  );
}

// Cruz direcional e botões A/B (só aparecem em tela de toque)
export default function Controles({ aoApertar }) {
  return (
    <div className="controles">
      <div className="dpad">
        <Botao tecla="ArrowUp" classe="seta cima" rotulo="Cima" aoApertar={aoApertar} />
        <Botao tecla="ArrowLeft" classe="seta esquerda" rotulo="Esquerda" aoApertar={aoApertar} />
        <span className="centro" />
        <Botao tecla="ArrowRight" classe="seta direita" rotulo="Direita" aoApertar={aoApertar} />
        <Botao tecla="ArrowDown" classe="seta baixo" rotulo="Baixo" aoApertar={aoApertar} />
      </div>

      <div className="botoes-acao">
        <div className="botao-acao b">
          <Botao tecla="Escape" classe="redondo" rotulo="B, sair" aoApertar={aoApertar} />
          <span>B &middot; SAIR</span>
        </div>
        <div className="botao-acao a">
          <Botao tecla="Enter" classe="redondo" rotulo="A, confirmar" aoApertar={aoApertar} />
          <span>A &middot; OK</span>
        </div>
      </div>
    </div>
  );
}
