import { useEffect, useRef } from "react";

import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import PhaseIndicator from "./components/PhaseIndicator";
import { useChatSession } from "./hooks/useChatSession";

import "./App.css";


function App() {
  const {
    messages,
    phase,
    isWaiting,
    isComplete,
    sendMessage,
    resetSession,
    startSession,
  } = useChatSession();

  const hasStarted = useRef(false);

  useEffect(() => {
    if (hasStarted.current) {
      return;
    }

    hasStarted.current = true;
    startSession();
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Socratic Tutor</h1>
        <button onClick={resetSession}>
          New session
        </button>
      </header>

      <PhaseIndicator
        phase={phase}
        visible={!isComplete && phase !== null}
      />

      <ChatWindow messages={messages} />

      <ChatInput
        onSend={sendMessage}
        disabled={isWaiting || isComplete}
      />
    </div>
  );
}

export default App;