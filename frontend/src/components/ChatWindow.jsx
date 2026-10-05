import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({ messages, isWaiting, before = null }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isWaiting]);

  return (
    <div className="chat-window">
      {before}

      {messages.map((msg, i) => (
        <MessageBubble
          key={i}
          role={msg.role}
          content={msg.content}
        />
      ))}

      {isWaiting && (
        <div className="thinking-indicator">
          <span className="thinking-dot">•</span>
          <span className="thinking-dot">•</span>
          <span className="thinking-dot">•</span>
          <span className="thinking-text">Thinking</span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}