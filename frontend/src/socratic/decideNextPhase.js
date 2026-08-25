const PHASE_ORDER = ["elenchus", "aporia", "maieutics", "dialectic", "reflection_exit"];

const HEDGE_WORDS = ["maybe", "i guess", "i don't know", "not sure", "i think so"];

function looksLikeHedging(answer) {
  const lower = answer.toLowerCase();
  const tooShort = answer.trim().split(/\s+/).length < 5;
  const hasHedge = HEDGE_WORDS.some((w) => lower.includes(w));
  return tooShort || hasHedge;
}

// Pure function: (current phase, student's answer, how many attempts already
// made in this phase) -> "stay" or the next phase name.
// Swapping this for a real LLM call later means keeping this exact signature.
export function decideNextPhase(currentPhase, studentAnswer, attemptCount) {
  const MAX_ATTEMPTS_PER_PHASE = 3;

  if (looksLikeHedging(studentAnswer) && attemptCount < MAX_ATTEMPTS_PER_PHASE - 1) {
    return "stay";
  }

  const currentIndex = PHASE_ORDER.indexOf(currentPhase);
  const isLastPhase = currentIndex === PHASE_ORDER.length - 1;
  return isLastPhase ? currentPhase : PHASE_ORDER[currentIndex + 1];
}