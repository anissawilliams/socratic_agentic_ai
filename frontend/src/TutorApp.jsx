import { useEffect, useRef, useState } from "react";

import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import PhaseTimer from "./components/PhaseTimer";
import ScenarioPanel from "./components/ScenarioPanel";
import { expireTutor, finishTutor } from "./api/timerClient";
import { useChatSession } from "./hooks/useChatSession";

import "./App.css";
import "./assets/ai-study.css";
import aiStudyAvatar from "./assets/ai-study-avatar.png";

function TutorApp({ onCompleted }) {
  const {
    messages,
    isWaiting,
    isComplete,
    sendMessage,
    resetSession,
    startSession,
  } = useChatSession();

  const hasStarted = useRef(false);
  const completionHandled = useRef(false);
  const [transitionError, setTransitionError] = useState("");
  const [timeUp, setTimeUp] = useState(false);
  const [canContinue, setCanContinue] = useState(false);
  const [continuing, setContinuing] = useState(false);

  // After the minimum time, the student may choose to move on.
  const handleContinue = async () => {
    setContinuing(true);
    try {
      await finishTutor();
      completionHandled.current = true;
      await onCompleted?.();
    } catch {
      setContinuing(false);
      setTransitionError("Could not move to the next part. Please try again.");
    }
  };

  // Time ran out: end the session on the server, then move to the post-test.
  const handleTimeUp = async () => {
    setTimeUp(true);
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        await expireTutor();
        break;
      } catch {
        // The server allows a few seconds of clock tolerance; try again shortly.
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    }
    completionHandled.current = true;
    onCompleted?.().catch(() => {
      setTransitionError("Time is up, but the next part could not be loaded.");
    });
  };
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
          <button
            className="new-session-button"
            onClick={resetSession}
          >
            New session
          </button>
        )}

      </header>

      {!isComplete && (
        <div className="tutor-timer">
          <PhaseTimer
            onExpire={handleTimeUp}
            onMinReached={() => setCanContinue(true)}
          />
          {canContinue && !timeUp && (
            <button
              type="button"
              className="tutor-continue"
              onClick={handleContinue}
              disabled={continuing || isWaiting}
            >
              {continuing ? "Moving on..." : "Continue to next step"}
            </button>
          )}
        </div>
      )}
      <ScenarioPanel />
      {timeUp && !isComplete && (
        <p className="tutor-time-up">Time is up. Moving on to the next part...</p>
      )}

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
        disabled={isWaiting || isComplete || timeUp || continuing}
      />
    </div>
  );
}

export default TutorApp;
