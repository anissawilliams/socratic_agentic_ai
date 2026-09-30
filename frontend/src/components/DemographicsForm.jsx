import { useState } from "react";

import "./AssessmentForm.css";

// Wording matches the approved demographics question list.
const GENDER_OPTIONS = [
  { code: "male", label: "Male" },
  { code: "female", label: "Female" },
  { code: "non_binary", label: "Non-binary" },
];

const RACE_OPTIONS = [
  { code: "white_european", label: "White / European" },
  { code: "black_african", label: "Black / African" },
  { code: "asian", label: "Asian" },
  { code: "hispanic_latino", label: "Hispanic / Latino" },
  { code: "middle_eastern_north_african", label: "Middle Eastern / North African" },
  { code: "other", label: "Another racial or ethnic background" },
];

export default function DemographicsForm({ onSubmit }) {
  const [age, setAge] = useState("");
  const [genderCode, setGenderCode] = useState("");
  const [raceCodes, setRaceCodes] = useState([]);
  const [otherDescription, setOtherDescription] = useState("");
  const [fieldOfStudy, setFieldOfStudy] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const toggleRace = (code) => {
    setRaceCodes((current) =>
      current.includes(code)
        ? current.filter((value) => value !== code)
        : [...current, code]
    );
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    const ageNumber = Number(age);
    if (!Number.isInteger(ageNumber) || ageNumber < 18 || ageNumber > 99) {
      setError("Please enter your age as a whole number between 18 and 99.");
      return;
    }
    if (raceCodes.length === 0) {
      setError("Please select at least one option for question 3.");
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        age: ageNumber,
        gender_code: genderCode,
        race_codes: raceCodes,
        race_other_description: raceCodes.includes("other")
          ? otherDescription.trim()
          : null,
        field_of_study: fieldOfStudy.trim(),
      });
    } catch (submissionError) {
      setError(submissionError.message);
      setSubmitting(false);
    }
  };

  return (
    <main className="assessment-shell">
      <form className="assessment-form" onSubmit={handleSubmit}>
        <header>
          <p className="assessment-form__eyebrow">Before you begin</p>
          <h1>About you</h1>
          <p>These questions are asked only once.</p>
        </header>

        <label className="assessment-form__question">
          <span>1. How old are you?</span>
          <span className="assessment-form__inline">
            <input
              type="number"
              inputMode="numeric"
              min={18}
              max={99}
              step={1}
              value={age}
              onChange={(event) => setAge(event.target.value)}
              required
            />
            years
          </span>
        </label>

        <fieldset className="assessment-form__question">
          <legend>2. What is your gender?</legend>
          {GENDER_OPTIONS.map((option) => (
            <label key={option.code} className="assessment-form__choice">
              <input
                type="radio"
                name="gender"
                value={option.code}
                checked={genderCode === option.code}
                onChange={() => setGenderCode(option.code)}
                required
              />
              {option.label}
            </label>
          ))}
        </fieldset>

        <fieldset className="assessment-form__question">
          <legend>
            3. How would you describe your racial and/or ethnic background?
            (Select all that apply.)
          </legend>
          {RACE_OPTIONS.map((option) => (
            <label key={option.code} className="assessment-form__choice">
              <input
                type="checkbox"
                value={option.code}
                checked={raceCodes.includes(option.code)}
                onChange={() => toggleRace(option.code)}
              />
              {option.label}
            </label>
          ))}
          {raceCodes.includes("other") && (
            <input
              type="text"
              aria-label="Describe your racial or ethnic background"
              maxLength={100}
              value={otherDescription}
              onChange={(event) => setOtherDescription(event.target.value)}
              required
            />
          )}
        </fieldset>

        <label className="assessment-form__question">
          <span>4. What is your field of study (major)?</span>
          <input
            type="text"
            className="assessment-form__wide"
            maxLength={100}
            value={fieldOfStudy}
            onChange={(event) => setFieldOfStudy(event.target.value)}
            required
          />
        </label>

        {error && <p className="assessment-form__error">{error}</p>}

        <div className="assessment-form__actions">
          <button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : "Continue"}
          </button>
        </div>
      </form>
    </main>
  );
}
