import { useRef, useState } from "react";

import PhaseTimer from "./PhaseTimer";

import "./AssessmentForm.css";


export default function AssessmentForm({ content, onSubmit, onTimeout, onSkip }) {
  const [answers, setAnswers] = useState({});
  const answersRef = useRef({});
  const [timedOut, setTimedOut] = useState(false);
  const [canContinue, setCanContinue] = useState(!onTimeout);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const isPreTest = content.stage === "pretest";

  const updateAnswer = (questionId, value) => {
    setAnswers((current) => {
      const next = { ...current, [questionId]: value };
      answersRef.current = next;
      return next;
    });
  };

  // Time ran out: save whatever the student has written, blanks included.
  const handleTimeout = async () => {
    setTimedOut(true);
    setError("");
    try {
      await onTimeout({
        instrument_key: content.instrument_key,
        attempt_id: content.attempt_id,
        stage: content.stage,
        answers: content.questions.map((question) => ({
          question_id: question.id,
          value: answersRef.current[question.id] || "",
        })),
      });
    } catch {
      setError("Time is up, but your answers could not be saved. Please refresh the page.");
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await onSubmit({
        instrument_key: content.instrument_key,
        instrument_version: content.instrument_version,
        attempt_id: content.attempt_id,
        content_sha256: content.content_sha256,
        stage: content.stage,
        scenario_key: content.scenario_key,
        answers: content.questions.map((question) => ({
          question_id: question.id,
          value: answers[question.id],
        })),
      });
    } catch (submissionError) {
      setError(submissionError?.message || "Your responses could not be saved.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="assessment-shell">
      <form className="assessment-form" onSubmit={handleSubmit}>
        {onTimeout && (
          <div className="assessment-form__timer">
            <PhaseTimer
              onExpire={handleTimeout}
              onMinReached={() => setCanContinue(true)}
            />
          </div>
        )}

        <header>
          <p className="assessment-form__eyebrow">
            {isPreTest ? "Before the conversation" : "After the conversation"}
          </p>
          <h1>{isPreTest ? "Pre-test" : "Post-test"}</h1>
          <p>No AI feedback is provided during this assessment.</p>
        </header>

        <section className="assessment-form__scenario">
          <h2>{content.scenario_title}</h2>
          <p>{content.scenario_text}</p>
        </section>

        {content.questions.map((question, index) => (
          <label className="assessment-form__question" key={question.id}>
            <span>
              {index + 1}. {question.prompt}
            </span>
            <textarea
              value={answers[question.id] || ""}
              onChange={(event) => updateAnswer(question.id, event.target.value)}
              rows={5}
              required
              disabled={timedOut}
            />
          </label>
        ))}

        {timedOut && !error && (
          <p className="assessment-form__notice">Time is up. Saving your answers...</p>
        )}

        {error && <p className="assessment-form__error">{error}</p>}

        <div className="assessment-form__actions">
          {onSkip && (
            <button type="button" onClick={onSkip}>
              Continue without submitting
            </button>
          )}
          <button
            type="submit"
            disabled={submitting || timedOut || !canContinue}
            title={canContinue ? undefined : "Available once the minimum time has passed"}
          >
            {submitting ? "Saving..." : "Submit responses"}
          </button>
        </div>
      </form>
    </main>
  );
}
