import { useState } from "react";

import { supabase } from "../api/supabase";
import { claimParticipantCode } from "../api/authClient";


export default function Auth({ session, onAuthenticated }) {
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSubmitting(true);
    setMessage("");

    try {
      let activeSession = session;

      if (!activeSession) {
        const { data, error } =
          await supabase.auth.signInAnonymously();

        if (error) {
          throw error;
        }

        activeSession = data.session;
      }

      if (!activeSession?.access_token) {
        throw new Error(
          "Could not create a secure study session."
        );
      }

      const participant = await claimParticipantCode(
        code,
        activeSession.access_token
      );

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