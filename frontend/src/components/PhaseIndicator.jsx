// Toggleable per our earlier conversation — visible={false} hides it
// without ripping it out, so it's easy to flip on for a research condition later.
export default function PhaseIndicator({ phase, visible = false }) {
    if (!visible) return null;
    return <div className="phase-indicator">Phase: {phase}</div>;
  }