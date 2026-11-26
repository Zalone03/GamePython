// ===========
// Tempo
// ===========

// Espera alguns milissegundos
export const esperar = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Espera o navegador desenhar o próximo quadro (com limite de 100 ms, se a aba estiver escondida)
export const proximoQuadro = () =>
  new Promise((resolve) => {
    const limite = setTimeout(resolve, 100);
    requestAnimationFrame(() => {
      clearTimeout(limite);
      resolve();
    });
  });

// ===========
// Identificadores
// ===========

// Gera um id único para cada partida
export const novoId = () => crypto.randomUUID?.() ?? String(Date.now() + Math.random());
