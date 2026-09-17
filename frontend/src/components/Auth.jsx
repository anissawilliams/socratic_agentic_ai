import { useState } from "react";

import { authenticateParticipant } from "../api/authClient";


export default function Auth({ onAuthenticated }) {
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSubmitting(true);
    setMessage("");

    try {
      const participant = await authenticateParticipant(code);

      onAuthenticated(participant);
    } catch (error) {
      const detail =
        error?.response?.data?.detail ||
        error?.message ||
        "Could not enter the study.";

      setMessage(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={code}
        onChange={(event) =>
          setCode(event.target.value.toUpperCase())
        }
        placeholder="Participant code"
        autoComplete="off"
        spellCheck="false"
        minLength={8}
        maxLength={64}
        required
      />

      <button type="submit" disabled={submitting}>
        {submitting ? "Entering..." : "Begin Study"}
      </button>

      {message && <p>{message}</p>}
    </form>
  );
}
