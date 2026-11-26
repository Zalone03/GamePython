import { useArcade } from "./hooks/useArcade";
import Tela from "./componentes/Tela";
import Controles from "./componentes/Controles";

// ===========
// Aplicativo
// ===========

// O portátil: a tela e, no celular, os controles embaixo dela
export default function App() {
  const arcade = useArcade();

  return (
    <main className="aparelho">
      <Tela arcade={arcade} />
      <Controles aoApertar={arcade.pressionar} />
    </main>
  );
}
