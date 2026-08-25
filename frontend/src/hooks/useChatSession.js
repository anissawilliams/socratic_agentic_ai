import { useState } from "react";
import { startSession as apiStartSession, sendMessage as apiSendMessage } from "../api/chatClient";

function generateSessionId() {
  return `session-${Date.now()}`;
}

export function useChatSession() {
  const [sessionId, setSessionId] = useState(generateSessionId());
  const [messages, setMessages] = useState([]);
  const [phase, setPhase] = useState("elenchus");
  const [attemptCount, setAttemptCount] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);

  const startSession = async (idOverride) => {
    const id = idOverride || sessionId;
    const data = await apiStartSession(id);
    setMessages([{ role: "tutor", content: data.message }]);
    setPhase(data.current_phase);
    setAttemptCount(data.attempt_count);
    setIsComplete(data.is_complete);
  };

  const sendMessage = async (text) => {
    setMessages((prev) => [...prev, { role: "student", content: text }]);
    setIsWaiting(true);
    try {
      const data = await apiSendMessage(sessionId, text);
      setMessages((prev) => [...prev, { role: "tutor", content: data.message }]);
      setPhase(data.current_phase);
      setAttemptCount(data.attempt_count);
      setIsComplete(data.is_complete);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "tutor", content: "Something went wrong reaching the tutor. Try again?" },
      ]);
    } finally {
      setIsWaiting(false);
    }
  };

  const resetSession = () => {
    const newId = generateSessionId();
    setSessionId(newId);
    setMessages([]);
    setPhase("elenchus");
    setAttemptCount(0);
    setIsComplete(false);
    startSession(newId); // pass the new id directly, don't rely on state having updated yet
  };

  return { messages, phase, isWaiting, isComplete, sendMessage, resetSession, startSession };
}