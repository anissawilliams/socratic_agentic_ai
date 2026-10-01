import { useEffect, useState } from "react";

import Auth from "./components/Auth";
import AssessmentForm from "./components/AssessmentForm";
import TutorApp from "./TutorApp";
import DemographicsForm from "./components/DemographicsForm";
import SurveyForm from "./components/SurveyForm";
import { submitDemographics } from "./api/studyFormsClient";
import { submitAssessmentOnTimeout } from "./api/timerClient";

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

  const devAuthBypass = import.meta.env.VITE_DEV_AUTH_BYPASS === "true";

  const refreshParticipant = async () => {
    const code = getStoredParticipantCode();

    if (!code) {
      setParticipant(null);
      return null;
    }

    const currentParticipant = await getParticipant(code);
    setParticipant(currentParticipant);
    return currentParticipant;
  };

  // The backend advances the study stage in the same transaction that saves
  // the final tutor turn, but retry briefly so a slow read never strands the
  // participant on a finished chat.
  const handleTutorComplete = async () => {
    for (let attempt = 0; attempt < 5; attempt++) {
      const current = await refreshParticipant();

      if (current?.study_status !== "tutor") {
        sessionStorage.removeItem("socratic_tutor_session");
        return current;
      }

      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    throw new Error("Post-test is not ready yet");
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
  if (participant.study_status === "demographics") {
    return (
      <DemographicsForm
        onSubmit={async (demographics) => {
          await submitDemographics(demographics);
          await refreshParticipant();
        }}
      />
    );
  }

  if (participant.study_status === "survey") {
    return <SurveyForm onSubmitted={refreshParticipant} />;
  }
  
  if (["pretest", "posttest"].includes(participant.study_status)) {
    if (assessmentLoading) {
      return <p>Loading assessment...</p>;
    }

    if (assessmentError) {
      return <p>{assessmentError}</p>;
    }

    if (!assessment) {
      return <p>Loading assessment...</p>;
    }

    return (
      <AssessmentForm
        content={assessment}
        onTimeout={async (payload) => {
          await submitAssessmentOnTimeout(payload);
          setAssessment(null);
          await refreshParticipant();
        }}
        onSubmit={async (submission) => {
          await submitAssessment(submission);
          setAssessment(null);
          try {
            await refreshParticipant();
          } catch (error) {
            console.error("Unable to load next study stage:", error);
            setAssessmentError(
              "Your responses were saved, but the next screen could not be loaded. Refresh this page to continue."
            );
          }
        }}
      />
    );
  }
  if (participant.study_status === "complete") {
    return (
      <main style={{ padding: "2rem" }}>
        <h1>Thank you</h1>
        <p>Your study session is complete.</p>
      </main>
    );
  }

  if (devAuthBypass || participant.study_status === "tutor") {
    return <TutorApp onCompleted={handleTutorComplete} />;
  }

  

  return (
    <main style={{ padding: "2rem" }}>
      <p>Study status is unavailable.</p>
    </main>
  );
}


export default App;
