import { useEffect, useState } from "react";

import Auth from "./components/Auth";
import TutorApp from "./TutorApp";

import { supabase } from "./api/supabase";
import { getParticipant } from "./api/authClient";

const DEV_AUTH_BYPASS =
  import.meta.env.DEV &&
  import.meta.env.VITE_DEV_AUTH_BYPASS === "true";

function App() {
  const [session, setSession] = useState(null);
  const [participant, setParticipant] = useState(null);
  const [authLoaded, setAuthLoaded] = useState(false);
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
    if (DEV_AUTH_BYPASS) {
      let active = true;

      const loadDevParticipant = async () => {
        try {
          const participant = await getParticipant();

          if (active) {
            setParticipant(participant);
          }
        } catch {
          if (active) {
            setAuthError(
              "Could not load the development participant. Check the backend bypass settings and enrollment."
            );
          }
        } finally {
          if (active) {
            setAuthLoaded(true);
          }
        }
      };

      loadDevParticipant();

      return () => {
        active = false;
      };
    }

    const loadAuth = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      setSession(session);

      if (session) {
        try {
          const participant = await getParticipant(
            session.access_token
          );

          setParticipant(participant);
        } catch {
          setAuthError("You are not authorized to access this study.");
        }
      }

      setAuthLoaded(true);
    };

    loadAuth();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      async (_event, newSession) => {
        setSession(newSession);
        setParticipant(null);
        setAuthError(null);

        if (newSession) {
          try {
            const participant = await getParticipant(
              newSession.access_token
            );

            setParticipant(participant);
          } catch {
            setAuthError(
              "You are not authorized to access this study."
            );
          }
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  if (!authLoaded) {
    return null;
  }

    if (!session && !DEV_AUTH_BYPASS) {
    return <Auth />;
  }

  if (authError) {
    return <p>{authError}</p>;
  }

  if (!participant) {
    return null;
  }

  return <TutorApp />;
}

export default App;