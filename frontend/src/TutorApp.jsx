import { useEffect, useRef, useState } from "react";

import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import SessionTimer from "./components/SessionTimer";
import { useChatSession } from "./hooks/useChatSession";
import SignOutLink from "./components/SignOutLink";

import "./App.css";
import "./assets/ai-study.css";
import aiStudyAvatar from "./assets/ai-study-avatar.png";

function TutorApp({ onCompleted }) {
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
  const completionHandled = useRef(false);
  const [transitionError, setTransitionError] = useState("");


  const sessionTime = "20:00";
  useEffect(() => {
    if (hasStarted.current) {
      return;
    }

    hasStarted.current = true;
    startSession();
  }, []);

  useEffect(() => {
    if (!isComplete || !onCompleted || completionHandled.current) {
      return;
    }

    completionHandled.current = true;
    onCompleted().catch((error) => {
      console.error("Unable to load post-test:", error);
      setTransitionError("The conversation is complete, but the post-test could not be loaded.");
    });
  }, [isComplete, onCompleted]);

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
            <h1 className="tutor-brand__name">Learning Study</h1>
            <span className="tutor-brand__status">
              Ready
            </span>
          </div>
        </div>

        {!isComplete && (
         <div className="header-links">
         {!isComplete && (
           <button type="button" className="header-link" onClick={resetSession}>
             New session
           </button>
         )}
         <SignOutLink variant="inline" />
       </div>
        )}

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

      {transitionError && (
        <div role="alert">
          <p>{transitionError}</p>
          <button type="button" onClick={() => {
            setTransitionError("");
            onCompleted().catch((error) => {
              console.error("Unable to load post-test:", error);
              setTransitionError("The post-test could not be loaded. Please try again.");
            });
          }}>
            Continue to post-test
          </button>
        </div>
      )}

      <ChatInput
        onSend={sendMessage}
        disabled={isWaiting || isComplete}
      />
    </div>
  );
}

export default TutorApp;
