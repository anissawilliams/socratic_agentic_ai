export default function PhaseIndicator({
  phase,
  visible = false,
}) {
  if (!visible || !phase) {
    return null;
  }

  return (
    <div className="phase-indicator">
      Phase: {phase}
    </div>
  );
}