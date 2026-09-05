import { useEffect, useState } from "react";

import Auth from "./components/Auth";
import TutorApp from "./TutorApp";
import { supabase } from "./api/supabase";

function App() {
  const [session, setSession] = useState(null);
  const [authLoaded, setAuthLoaded] = useState(false);

  useEffect(() => {
    const loadSession = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      setSession(session);
      setAuthLoaded(true);
    };

    loadSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
    });

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

  return <TutorApp />;
}

export default App;