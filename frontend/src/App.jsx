import { useEffect, useState } from "react";

import Auth from "./components/Auth";
import TutorApp from "./TutorApp";

import {
  clearParticipantCode,
  getParticipant,
  getStoredParticipantCode,
} from "./api/authClient";


function App() {
  const [participant, setParticipant] = useState(null);
  const [authLoaded, setAuthLoaded] = useState(false);

  useEffect(() => {
    let active = true;

    const loadAuth = async () => {
      const code = getStoredParticipantCode();

      if (code) {
        try {
          const participant = await getParticipant(code);

          if (active) {
            setParticipant(participant);
          }
        } catch (error) {
          console.error("Unable to restore participant:", error);
        
          const status = error?.response?.status;
        
          if (status === 401 || status === 403) {
            clearParticipantCode();
          }
        
          if (active) {
            setParticipant(null);
          }
        }
      }

      if (active) {
        setAuthLoaded(true);
      }
    };

    loadAuth();

    return () => {
      active = false;
    };
  }, []);

  if (!authLoaded) {
    return null;
  }

  if (!participant) {
    return (
      <Auth
        onAuthenticated={(participant) => {
          setParticipant(participant);
        }}
      />
    );
  }

  return <TutorApp />;
}


export default App;
