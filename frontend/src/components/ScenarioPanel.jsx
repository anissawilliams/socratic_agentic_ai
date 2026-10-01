import { useEffect, useState } from "react";
import axios from "axios";

import { getStoredParticipantCode } from "../api/authClient";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function ScenarioPanel() {
  const [scenario, setScenario] = useState(null);

  useEffect(() => {
    axios
      .get(`${API_BASE}/tutor/scenario`, {
        headers: { "X-Participant-Code": getStoredParticipantCode() },
      })
      .then((response) => setScenario(response.data))
      .catch(() => setScenario(null));
  }, []);

  if (!scenario) return null;

  return (
    <details className="scenario-panel" open>
      <summary>
        <span className="scenario-panel__label">Scenario</span>
        <span className="scenario-panel__title">{scenario.title}</span>
      </summary>
      <div className="scenario-panel__text">{scenario.text}</div>
    </details>
  );
}