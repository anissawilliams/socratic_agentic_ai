export default function MessageBubble({ role, content }) {
    const isStudent = role === "student";
    return (
      <div className={`bubble-row ${isStudent ? "student" : "tutor"}`}>
        <div className={`bubble ${isStudent ? "bubble-student" : "bubble-tutor"}`}>
          {content}
        </div>
      </div>
    );
  }