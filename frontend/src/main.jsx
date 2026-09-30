import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";
import SignOutLink from "./components/SignOutLink.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
    <SignOutLink />
  </StrictMode>
);
