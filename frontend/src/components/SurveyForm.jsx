import { useEffect, useState } from "react";

import { getSurvey, submitSurvey } from "../api/studyFormsClient";
import "./AssessmentForm.css";

export default function SurveyForm({ onSubmitted }) {
  const [survey, setSurvey] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [ratings, setRatings] = useState({});
  const [openAnswers, setOpenAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getSurvey()
      .then(setSurvey)
      .catch(() => setLoadError("The survey could not be loaded. Please refresh the page."));
  }, []);

  if (loadError) return <p>{loadError}</p>;
  if (!survey) return <p>Loading survey...</p>;

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (survey.likert.some((item) => !ratings[item.id])) {
      setError("Please answer every rating question.");
      return;
    }
    if (survey.open.some((item) => !(openAnswers[item.id] || "").trim())) {
      setError("Please answer both written questions.");
      return;
    }

    setSubmitting(true);
    try {
      await submitSurvey({
        instrument_key: survey.instrument_key,
        instrument_version: survey.instrument_version,
        likert: survey.likert.map((item) => ratings[item.id]),
        open_responses: survey.open.map((item) => openAnswers[item.id].trim()),
      });
      await onSubmitted();
    } catch (submissionError) {
      setError(submissionError.message);
      setSubmitting(false);
    }
  };

  return (
    <main className="assessment-shell">
      <form className="assessment-form" onSubmit={handleSubmit}>
        <header>
          <p className="assessment-form__eyebrow">Almost done</p>
          <h1>A few questions about your experience</h1>
          {survey.intro && <p>{survey.intro}</p>}
        </header>

        {survey.likert.map((item, index) => (
          <fieldset className="assessment-form__question" key={item.id}>
            <legend>
              {index + 1}. {item.prompt}
            </legend>
            <div className="assessment-form__scale">
              {survey.scale.map((label, scaleIndex) => (
                <label key={label} className="assessment-form__choice">
                  <input
                    type="radio"
                    name={item.id}
                    value={scaleIndex + 1}
                    checked={ratings[item.id] === scaleIndex + 1}
                    onChange={() =>
                      setRatings((current) => ({ ...current, [item.id]: scaleIndex + 1 }))
                    }
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
        ))}

        {survey.open.map((item, index) => (
          <label className="assessment-form__question" key={item.id}>
            <span>
              {survey.likert.length + index + 1}. {item.prompt}
            </span>
            <textarea
              rows={4}
              maxLength={5000}
              required
              value={openAnswers[item.id] || ""}
              onChange={(event) =>
                setOpenAnswers((current) => ({ ...current, [item.id]: event.target.value }))
              }
            />
          </label>
        ))}

        {error && <p className="assessment-form__error">{error}</p>}

        <div className="assessment-form__actions">
          <button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : "Submit"}
          </button>
        </div>
      </form>
    </main>
  );
}
