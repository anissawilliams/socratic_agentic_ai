import { useEffect, useState } from "react";

import Auth from "./components/Auth";
import AssessmentForm from "./components/AssessmentForm";
import TutorApp from "./TutorApp";

import {
  clearParticipantCode,
  getParticipant,
  getStoredParticipantCode,
} from "./api/authClient";

import {
  startAssessment,
  submitAssessment,
} from "./api/assessmentClient";


function App() {
  const [participant, setParticipant] = useState(null);
  const [authLoaded, setAuthLoaded] = useState(false);

  const [assessment, setAssessment] = useState(null);
  const [assessmentLoading, setAssessmentLoading] = useState(false);
  const [assessmentError, setAssessmentError] = useState("");

  const refreshParticipant = async () => {
    const code = getStoredParticipantCode();

    if (!code) {
      setParticipant(null);
      return;
    }

    const currentParticipant = await getParticipant(code);
    setParticipant(currentParticipant);
  };

  useEffect(() => {
    let active = true;

    const loadAuth = async () => {
      const code = getStoredParticipantCode();

      if (code) {
        try {
          const currentParticipant = await getParticipant(code);

          if (active) {
            setParticipant(currentParticipant);
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

  useEffect(() => {
    let active = true;

    const loadAssessment = async () => {
      if (
        !participant ||
        !["pretest", "posttest"].includes(participant.study_status)
      ) {
        if (active) {
          setAssessment(null);
        }
        return;
      }

      setAssessmentLoading(true);
      setAssessmentError("");

      try {
        const content = await startAssessment();

        if (active) {
          setAssessment(content);
        }
      } catch (error) {
        console.error("Unable to load assessment:", error);

        if (active) {
          setAssessmentError(
            error?.response?.data?.detail ||
              "The assessment could not be loaded."
          );
        }
      } finally {
        if (active) {
          setAssessmentLoading(false);
        }
      }
    };

    loadAssessment();

    return () => {
      active = false;
    };
  }, [participant?.study_status]);

  if (!authLoaded) {
    return null;
  }

  if (!participant) {
    return (
      <Auth
        onAuthenticated={(authenticatedParticipant) => {
          setParticipant(authenticatedParticipant);
        }}
      />
    );
  }

  if (["pretest", "posttest"].includes(participant.study_status)) {
    if (assessmentLoading) {
      return <p>Loading assessment...</p>;
    }

    if (assessmentError) {
      return <p>{assessmentError}</p>;
    }

    if (!assessment) {
      return null;
    }

    return (
      <AssessmentForm
        content={assessment}
        onSubmit={async (submission) => {
          await submitAssessment(submission);
          setAssessment(null);
          await refreshParticipant();
        }}
      />
    );
  }

  if (participant.study_status === "tutor") {
    return <TutorApp />;
  }

  if (participant.study_status === "complete") {
    return (
      <main style={{ padding: "2rem" }}>
        <h1>Thank you</h1>
        <p>Your study session is complete.</p>
      </main>
    );
  }

  return (
    <main style={{ padding: "2rem" }}>
      <p>Study status is unavailable.</p>
    </main>
  );
}


export default App;