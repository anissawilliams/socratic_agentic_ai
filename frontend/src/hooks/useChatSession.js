import { useState } from "react";
import {
  startSession as apiStartSession,
  sendMessage as apiSendMessage,
} from "../api/chatClient";


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

      setMessages((prev) => [
        ...prev,
        {
          role: "tutor",
          content: data.message,
        },
      ]);

      setPhase(data.current_phase);
      setPhaseAttemptCount(data.phase_attempt_count);
      setIsComplete(data.is_complete);
    } catch (err) {
      console.error("Tutor request failed:", err);

      setMessages((prev) => [
        ...prev,
        {
          role: "tutor",
          content: "Something went wrong reaching the tutor. Try again?",
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