import { useEffect, useState } from "react";

import { clearParticipantCode, getStoredParticipantCode } from "../api/authClient";

export default function SignOutLink({ variant = "floating" }) {
  const [signedIn, setSignedIn] = useState(() => Boolean(getStoredParticipantCode()));

  useEffect(() => {
    const update = () => setSignedIn(Boolean(getStoredParticipantCode()));
    window.addEventListener("participant-code-changed", update);
    return () => window.removeEventListener("participant-code-changed", update);
  }, []);

  if (!signedIn) return null;

  const signOut = () => {
    clearParticipantCode();
    sessionStorage.removeItem("socratic_tutor_session");
    window.location.reload();
  };

  return (
    <button
      type="button"
      className={variant === "inline" ? "header-link" : "sign-out-link"}
      onClick={signOut}
    >
      {variant === "inline" ? "Sign out" : "Not you? Sign out"}
    </button>
  );
}