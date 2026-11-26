import { useEffect, useRef, useState } from "react";
import { carregarPython, suportaPython } from "../python/motor";
import { esperar } from "../util/utilidades";

// ===========
// Abertura
// ===========

// Sequência de abertura: escreve as linhas do "sistema" e carrega o Python
export function useInicializacao(totalJogos) {
  // Linhas mostradas na tela durante a abertura
  const [linhas, setLinhas] = useState([]);

  // "carregando", "pronto" ou "erro"
  const [estado, setEstado] = useState("carregando");

  // Vira true quando o jogador aperta uma tecla (pula a animação)
  const pularRef = useRef(false);

  useEffect(() => {
    let cancelado = false;
    setLinhas([]);

    // Acrescenta linhas prontas no fim
    const adicionar = (...novas) => setLinhas((l) => [...l, ...novas]);

    // Completa a última linha (ex.: "Carregando Python... OK")
    const completarUltima = (sufixo, classe) =>
      setLinhas((l) => [...l.slice(0, -1), { texto: l.at(-1).texto + sufixo, classe: classe ?? l.at(-1).classe }]);

    // Escreve uma linha letra por letra
    async function digitar(texto, classe = "", velocidade = 14) {
      adicionar({ texto: "", classe });
      for (let i = 1; i <= texto.length; i++) {
        if (cancelado) return;
        if (pularRef.current) i = texto.length;
        const parcial = texto.slice(0, i);
        setLinhas((l) => [...l.slice(0, -1), { texto: parcial, classe }]);
        if (!pularRef.current) await esperar(velocidade);
      }
    }

    // Mostra o erro de navegador sem suporte
    function erroDeNavegador() {
      adicionar(
        { texto: "ERRO: este navegador não consegue rodar Python.", classe: "erro" },
        { texto: "Use o Chrome ou o Edge atualizados." },
      );
      setEstado("erro");
    }

    // Mostra o erro de download do Python
    function erroDeDownload() {
      completarUltima("FALHOU", "erro");
      adicionar(
        { texto: "" },
        { texto: "Na primeira vez o Python é baixado da internet." },
        { texto: "Verifique a conexão e recarregue a página (F5)." },
      );
      setEstado("erro");
    }

    // Roda a abertura inteira
    async function abrir() {
      await esperar(400);
      if (cancelado) return;
      await digitar("GAMEPYTHON OS v1.0  (c) 2026", "sistema");
      await digitar("Verificando memória.......... 640K OK");

      if (!suportaPython()) return erroDeNavegador();

      await digitar("Carregando Python............ ");
      try {
        await carregarPython();
      } catch {
        if (!cancelado) erroDeDownload();
        return;
      }
      if (cancelado) return;
      completarUltima("OK");

      await digitar(`Lendo cartuchos.............. ${totalJogos} encontrados`);
      if (!pularRef.current) await esperar(400);
      if (!cancelado) setEstado("pronto");
    }

    abrir();

    // Cancela a abertura se o componente sair da tela
    return () => {
      cancelado = true;
    };
  }, [totalJogos]);

  // Acelera a abertura
  const pular = () => {
    pularRef.current = true;
  };

  return { linhas, estado, pular };
}
