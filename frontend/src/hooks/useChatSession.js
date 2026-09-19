import { useEffect, useState } from "react";

import {
  startSession as apiStartSession,
  sendMessage as apiSendMessage,
} from "../api/chatClient";

import { clearParticipantCode } from "../api/authClient";

const STORAGE_KEY = "socratic_tutor_session";


function loadStoredSession() {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return null;
    }

    return JSON.parse(stored);
  } catch {
    sessionStorage.removeItem(STORAGE_KEY);
    return null;
  }
}


function failureMessage(err) {
  if (err.status === null || err.status === undefined) {
    return "Can't reach the tutor. Check that the backend is running, then try again.";
  }

  if (err.status === 401 || err.status === 403) {
    return "Your participant code could not be verified. Please sign in again.";
  }

  if (err.status === 404) {
    return "This tutoring session could not be found. Start a new session to continue.";
  }

  if (err.status >= 500) {
    return "The tutor hit an error while generating a reply. The details are in the backend log.";
  }

  return `The tutor rejected the request (status ${err.status}).`;
}

function recoverFromAuthFailure(err) {
  if (err.status !== 401 && err.status !== 403) {
    return false;
  }

  clearParticipantCode();
  sessionStorage.removeItem(STORAGE_KEY);

  window.location.reload();

  return true;
}

function logFailure(action, err) {
  console.error(
    `${action} failed — status ${err.status ?? "no response"}:`,
    err.detail ?? err.message,
    err.cause ?? err
  );
}


export function useChatSession() {
  const [storedSession] = useState(() => loadStoredSession());

  const [sessionId, setSessionId] = useState(
    () => storedSession?.sessionId ?? null
  );

  const [messages, setMessages] = useState(
    () => storedSession?.messages ?? []
  );

  const [phase, setPhase] = useState(
    () => storedSession?.phase ?? null
  );

  const [phaseAttemptCount, setPhaseAttemptCount] = useState(
    () => storedSession?.phaseAttemptCount ?? 0
  );

  const [isComplete, setIsComplete] = useState(
    () => storedSession?.isComplete ?? false
  );

  const [isWaiting, setIsWaiting] = useState(false);


  useEffect(() => {
    if (!sessionId) {
      return;
    }

    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        sessionId,
        messages,
        phase,
        phaseAttemptCount,
        isComplete,
      })
    );
  }, [
    sessionId,
    messages,
    phase,
    phaseAttemptCount,
    isComplete,
  ]);


  const startSession = async () => {
    if (sessionId) {
      return;
    }

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
      setPhaseAttemptCount(data.phase_attempt_count ?? 0);
      setIsComplete(data.is_complete);
    } catch (err) {
      logFailure("Starting a session", err);
      if (recoverFromAuthFailure(err)) {
        return;
      }
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
      const data = await apiSendMessage(
        sessionId,
        text
      );

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
      setPhaseAttemptCount(
        data.phase_attempt_count ?? 0
      );
      setIsComplete(data.is_complete);
    } catch (err) {
      logFailure("Sending a message", err);
      if (recoverFromAuthFailure(err)) {
        return;
      }
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
    sessionStorage.removeItem(STORAGE_KEY);

    setSessionId(null);
    setMessages([]);
    setPhase(null);
    setPhaseAttemptCount(0);
    setIsComplete(false);

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
      setPhaseAttemptCount(data.phase_attempt_count ?? 0);
      setIsComplete(data.is_complete);
    } catch (err) {
      logFailure("Starting a session", err);
      if (recoverFromAuthFailure(err)) {
        return;
      }
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