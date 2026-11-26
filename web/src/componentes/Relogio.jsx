import { useEffect, useState } from "react";

// ===========
// Relógio
// ===========

// Hora atual no formato 15:42
function horaAgora() {
  return new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

// Relógio da barra de status, atualizado a cada 10 segundos
export default function Relogio() {
  const [hora, setHora] = useState(horaAgora);

  useEffect(() => {
    const timer = setInterval(() => setHora(horaAgora()), 10_000);
    return () => clearInterval(timer);
  }, []);

  return <span>{hora}</span>;
}
