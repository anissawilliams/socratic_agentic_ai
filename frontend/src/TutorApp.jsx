import { useEffect, useRef } from "react";

import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import PhaseIndicator from "./components/PhaseIndicator";
import { useChatSession } from "./hooks/useChatSession";

import "./App.css";
import "./assets/socratic-tutor.css";
import socratesAvatar from "./assets/socrates-avatar.png";


function TutorApp() {
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
        <div className="tutor-brand">
          <img
            src={socratesAvatar}
            alt=""
            className="tutor-brand__avatar"
          />

          <div className="tutor-brand__text">
            <h1 className="tutor-brand__name">Socratic Tutor</h1>
            <span className="tutor-brand__status">
              Ready to explore
            </span>
          </div>
        </div>

        <button
          className="new-session-button"
          onClick={resetSession}
        >
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

export default TutorApp;