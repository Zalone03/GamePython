import { useEffect, useRef } from "react";

// ===========
// Teclado
// ===========

// Escuta as teclas da página inteira e chama sempre a versão mais nova de aoTeclar
export function useTeclado(aoTeclar) {
  // Guarda a função atual (com o estado atual) sem recriar o ouvinte
  const funcaoRef = useRef(aoTeclar);
  funcaoRef.current = aoTeclar;

  useEffect(() => {
    // Repassa cada tecla para a função guardada
    const ouvir = (e) => funcaoRef.current(e);
    window.addEventListener("keydown", ouvir);
    return () => window.removeEventListener("keydown", ouvir);
  }, []);
}
