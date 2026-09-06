import { useEffect, useState } from "react";

import Auth from "./components/Auth";
import TutorApp from "./TutorApp";

import { supabase } from "./api/supabase";
import { getParticipant } from "./api/authClient";

function App() {
  const [session, setSession] = useState(null);
  const [participant, setParticipant] = useState(null);
  const [authLoaded, setAuthLoaded] = useState(false);
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
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

  if (!session) {
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