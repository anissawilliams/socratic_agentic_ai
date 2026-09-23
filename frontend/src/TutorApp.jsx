import { useEffect, useRef } from "react";

import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import SessionTimer from "./components/SessionTimer";
import { useChatSession } from "./hooks/useChatSession";
import { clearParticipantCode } from "./api/authClient";

import "./App.css";
import "./assets/ai-study.css";
import aiStudyAvatar from "./assets/ai-study-avatar.png";

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


  const sessionTime = "20:00";
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
            src={aiStudyAvatar}
            alt=""
            className="tutor-brand__avatar"
          />

          <div className="tutor-brand__text">
            <h1 className="tutor-brand__name">AI Study</h1>
            <span className="tutor-brand__status">
              Ready
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

      <SessionTimer
        sessionTime={sessionTime}
        visible={true}
        phase={phase}
        isComplete={isComplete}
      />

      <ChatWindow messages={messages}
      isWaiting={isWaiting}
      />

      <ChatInput
        onSend={sendMessage}
        disabled={isWaiting || isComplete}
      />
    </div>
  );
}

export default TutorApp;