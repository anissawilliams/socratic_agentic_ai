import ReactMarkdown from "react-markdown";

export default function MessageBubble({ role, content }) {
  const isStudent = role === "student";

  return (
    <div className={`bubble-row ${isStudent ? "student" : "tutor"}`}>
      <div className={`bubble ${isStudent ? "bubble-student" : "bubble-tutor"}`}>
        {isStudent ? content : <ReactMarkdown>{content}</ReactMarkdown>}
      </div>
    </div>
  );
}