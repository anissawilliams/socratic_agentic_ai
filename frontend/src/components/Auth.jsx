import { useState } from "react";

import { authenticateParticipant } from "../api/authClient";
import "./Auth.css";

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
      const status = error?.response?.status;
      setMessage(
        status === 401 || status === 403
          ? "That code wasn't recognized. Please check it and try again."
          : "Something went wrong. Please try again in a moment."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="auth-shell">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Welcome</h1>
        <p>Enter the participant code you were given to begin.</p>

        <label className="auth-card__label" htmlFor="participant-code">
          Participant code
        </label>
        <input
          id="participant-code"
          className="auth-card__input"
          type="text"
          value={code}
          onChange={(event) => setCode(event.target.value.toUpperCase())}
          placeholder="TEST-XXXX-XXXX"
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck="false"
          minLength={8}
          maxLength={64}
          required
          autoFocus
        />

        <button className="auth-card__button" type="submit" disabled={submitting}>
          {submitting ? "Entering..." : "Begin"}
        </button>

        {message && <p className="auth-card__error">{message}</p>}
      </form>
    </main>
  );
}