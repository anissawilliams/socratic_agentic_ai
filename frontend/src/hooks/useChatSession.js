import { useState } from "react";
import {
  startSession as apiStartSession,
  sendMessage as apiSendMessage,
} from "../api/chatClient";


function failureMessage(err) {
  if (err.status === null || err.status === undefined) {
    return "Can't reach the tutor. Check that the backend is running, then try again.";
  }

  if (err.status === 401 || err.status === 403) {
    return "Your sign-in expired. Reload the page to sign in again.";
  }

  if (err.status === 404) {
    return "This session is no longer on the server, which happens when the backend restarts. Start a new session to continue.";
  }

  if (err.status >= 500) {
    return "The tutor hit an error while generating a reply. The details are in the backend log.";
  }

  return `The tutor rejected the request (status ${err.status}).`;
}

function logFailure(action, err) {
  console.error(
    `${action} failed — status ${err.status ?? "no response"}:`,
    err.detail ?? err.message,
    err.cause ?? err
  );
}

export function useChatSession() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [phase, setPhase] = useState(null);
  const [phaseAttemptCount, setPhaseAttemptCount] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);


  const startSession = async () => {
    setIsWaiting(true);

    try {
      const data = await apiStartSession();

      setSessionId(data.session_id);
      setMessages([
        {
          role: "tutor",
          content: data.message,
        },
      ]);
      setPhase(data.current_phase);
      setPhaseAttemptCount(data.phase_attempt_count);
      setIsComplete(data.is_complete);
    } catch (err) {
      logFailure("Starting a session", err);

      setMessages([
        {
          role: "tutor",
          content: failureMessage(err),
        },
      ]);
    } finally {
      setIsWaiting(false);
    }
  };


  const sendMessage = async (text) => {
    if (!sessionId || isComplete) {
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        role: "student",
        content: text,
      },
    ]);

    setIsWaiting(true);

    try {
      const data = await apiSendMessage(sessionId, text);

      if (data.message) {
        setMessages((prev) => [
          ...prev,
          {
            role: "tutor",
            content: data.message,
          },
        ]);
      }

      setPhase(data.current_phase);
      setPhaseAttemptCount(data.phase_attempt_count);
      setIsComplete(data.is_complete);
    } catch (err) {
      logFailure("Sending a message", err);

      setMessages((prev) => [
        ...prev,
        {
          role: "tutor",
          content: failureMessage(err),
        },
      ]);
    } finally {
      setIsWaiting(false);
    }
  };


  const resetSession = async () => {
    setSessionId(null);
    setMessages([]);
    setPhase(null);
    setPhaseAttemptCount(0);
    setIsComplete(false);

    await startSession();
  };


  return {
    sessionId,
    messages,
    phase,
    phaseAttemptCount,
    isWaiting,
    isComplete,
    sendMessage,
    resetSession,
    startSession,
  };
}
