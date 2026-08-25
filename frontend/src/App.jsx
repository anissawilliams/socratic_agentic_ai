import { useEffect } from "react";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import PhaseIndicator from "./components/PhaseIndicator";
import { useChatSession } from "./hooks/useChatSession";
import "./App.css";

function App() {
  const { messages, phase, isWaiting, isComplete, sendMessage, resetSession, startSession } = useChatSession();

  useEffect(() => {
    startSession();
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Socratic Tutor</h1>
        <button onClick={resetSession}>New session</button>
      </header>

      <PhaseIndicator phase={phase} visible={true} />

      <ChatWindow messages={messages} />

      <ChatInput onSend={sendMessage} disabled={isWaiting || isComplete} />
    </div>
  );
}

export default App;