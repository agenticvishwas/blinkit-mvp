import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ConciergeProvider } from "./state/ConciergeContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConciergeProvider>
      <App />
    </ConciergeProvider>
  </React.StrictMode>
);
