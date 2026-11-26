import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./estilos/base.css";
import "./estilos/tela.css";
import "./estilos/terminal.css";
import "./estilos/controles.css";

// ===========
// Início
// ===========

// Liga o React na div #root do index.html
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
