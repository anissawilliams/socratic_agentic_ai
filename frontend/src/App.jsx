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
              "Could not load the development participant. " +
              "Check the backend bypass settings and enrollment."
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

    let active = true;

    const loadAuth = async () => {
      const {
        data: { session },
        error,
      } = await supabase.auth.getSession();

      if (!active) {
        return;
      }

      if (error) {
        setAuthError("Could not restore the study session.");
        setAuthLoaded(true);
        return;
      }

      setSession(session);

      if (session) {
        try {
          const participant = await getParticipant(
            session.access_token
          );

          if (active) {
            setParticipant(participant);
          }
        } catch (error) {
          if (active) {
            setParticipant(null);

            // 403 is expected for an authenticated anonymous
            // user who has not claimed a participant code yet.
            if (error?.response?.status !== 403) {
              setAuthError(
                "Could not restore the study participant."
              );
            }
          }
        }
      }

      if (active) {
        setAuthLoaded(true);
      }
    };

    loadAuth();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      (event, newSession) => {
        if (!active) {
          return;
        }

        setSession(newSession);
        setAuthError(null);

        if (event === "SIGNED_OUT" || !newSession) {
          setParticipant(null);
        }
      }
    );

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  if (!authLoaded) {
    return null;
  }

  if (authError) {
    return <p>{authError}</p>;
  }

  if (!participant && !DEV_AUTH_BYPASS) {
    return (
      <Auth
        session={session}
        onAuthenticated={(participant) => {
          setParticipant(participant);
          setAuthError(null);
        }}
      />
    );
  }

  if (!participant) {
    return null;
  }

  return <TutorApp />;
}


export default App;