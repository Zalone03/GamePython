// ===========
// Menu
// ===========

// Lista de jogos para escolher (o marcado fica com o fundo escuro)
export default function Menu({ jogos, selecionado, aoClicar }) {
  return (
    <>
      <div className="titulo">== ESCOLHA SEU JOGO ==</div>

      <ul className="menu">
        {jogos.map((jogo, i) => (
          <li key={jogo.id} className={i === selecionado ? "ativo" : ""} onClick={() => aoClicar(i)}>
            <span className="seta">&#9654;</span>
            <span>[{i + 1}]</span>
            <span>{jogo.nome}</span>
            <span className="desc">{jogo.descricao}</span>
          </li>
        ))}
      </ul>

      <div className="dica">Use ↑/↓ (ou 1-9) e aperte ENTER</div>
      <div className="piscando">- INSERT COIN -</div>
    </>
  );
}
