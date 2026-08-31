## Study deployment considerations

- Decide LangSmith tracing strategy for production study:
  - trace all sessions
  - sample a percentage of sessions
  - pilot/debug only
- Estimate LangSmith trace volume for ~300 participants.
- Confirm current LangSmith free-tier / paid limits before launch.
- Keep Supabase as the authoritative research dataset regardless of tracing strategy.
- Decide whether prompt/input/output content should be retained in LangSmith during the study.
- Document retention/privacy settings before participant data collection.
- Load-test expected peak concurrency (~150 users).
- Finalize OpenAI + hosting + tracing cost estimate before deployment.

- Explore LangSmith evaluator templates for:
  - Socratic role fidelity
  - routing appropriateness
  - direct-answer leakage
  - trajectory coherence
  - conceptual refinement
- Validate LLM-as-judge scores against a human-coded subset before using them as research outcomes.


