export default function SessionTimer({
  sessionTime,
  visible = false,
  phase,
  isComplete,
}) {
  return (
    <div className="session-timer">
      Session time: {sessionTime}
    </div>
  );
}