# Socratic Tutor TODO

## 1. Study Flow

- [ ] Make the participant flow round-aware using `study_participation.round_number`
  - [ ] Round 1: demographics → pretest → assigned AI condition → posttest → complete
  - [ ] Round 2: pretest → assigned AI condition → posttest → final survey → complete
- [ ] Ensure demographics only appear in Round 1
- [ ] Ensure the final survey only appears in Round 2
- [ ] Ensure returning participants resume at the correct point instead of restarting completed steps
- [ ] Verify assessment attempts resume cleanly after refresh/re-entry
- [ ] Make sure the participant-facing UI never exposes internal study stage names

## 2. Conditions and Tutor Routing

- [ ] Clean up and finalize condition codes
  - [ ] Choose canonical condition codes
  - [ ] Update database values
  - [ ] Update seed/import scripts
  - [ ] Update tutor routing
  - [ ] Update logging
  - [ ] Remove temporary/inconsistent condition names
- [ ] Keep condition names hidden from participants
- [ ] Finalize the second/control AI condition after receiving methodological direction
- [ ] Keep the participant UI identical across conditions
- [ ] Route tutor behavior from `assigned_condition_code`
- [ ] Keep condition-specific behavior in prompts/configuration rather than duplicating the entire UI
- [ ] Confirm both conditions log comparable interaction data
- [ ] Keep the pedagogical treatment consistent across rounds; change scenario-specific content rather than redesigning the intervention

## 3. Round 1 Demographics

- [ ] Add a one-time demographics form before the Round 1 pretest
- [ ] Store demographic responses against the appropriate study subject/participant
- [ ] Add age as a numeric integer with validation
- [ ] Include gender
- [ ] Do not collect political affiliation
- [ ] Keep topic familiarity out of demographics
- [ ] Prevent duplicate demographic submissions
- [ ] Automatically skip demographics if already completed
- [ ] Make the form screenshot-ready for IRB materials

## 4. Round 2 Final Survey

- [ ] Review the previous Java Tutor survey
- [ ] Reuse/adapt appropriate questions rather than reinventing them
- [ ] Target approximately 4 Likert-scale questions plus 1 open-ended response
- [ ] Add the survey after the Round 2 posttest
- [ ] Store survey responses
- [ ] Prevent duplicate survey submissions
- [ ] Mark the participation complete after successful survey submission
- [ ] Add a clean study-complete screen

## 5. Timer

- [ ] Replace the placeholder `Session time: 20:00` with a real countdown
- [ ] Decide which activities are timed
  - [ ] Tutor interaction target: ~20 minutes
  - [ ] Decide whether pretest/posttest also need countdowns
- [ ] Decide what happens at `0:00`
  - [ ] Auto-submit
  - [ ] Disable further input
  - [ ] Or show a neutral `Time is up` state
- [ ] Persist or derive timing from a stable start timestamp so refreshes do not reset the timer
- [ ] Keep the timer visually neutral and non-distracting
- [ ] Log timing information needed for analysis

## 6. Keep Students On Task

- [ ] Add shared topic-scoping guardrails for both AI conditions
- [ ] Restrict interaction to the assigned scenario/task
- [ ] Redirect off-topic questions back to the assigned activity instead of answering unrelated requests
- [ ] Keep topic restriction separate from the Socratic treatment so it does not become a condition difference
- [ ] Consider logging off-topic/redirection events for later analysis
- [ ] Confirm prompts do not reveal condition names or study hypotheses

## 7. LLM-as-Judge / NLP Evaluation

- [ ] Define the evaluation rubric with Navid/Saber
- [ ] Create scenario-specific scoring criteria
- [ ] Decide what will be evaluated
  - [ ] Pretest/posttest final responses
  - [ ] Interaction/reasoning process
  - [ ] Both
- [ ] Implement LLM-as-judge as an analysis layer after interaction data is stored
- [ ] Store evaluator outputs separately from participant-generated data
- [ ] Store model name/version with each evaluation
- [ ] Store evaluator prompt version
- [ ] Store rubric version
- [ ] Preserve enough metadata for reproducibility
- [ ] Add complementary NLP/interaction metrics where useful
  - [ ] Turn count
  - [ ] Participant response length
  - [ ] Tutor response length
  - [ ] Response latency
  - [ ] Question/response patterns
  - [ ] Other semantic or linguistic measures selected by the research team
- [ ] Do not make LLM evaluation part of the live participant interaction unless there is a study-design reason to do so

## 8. UI / Participant Experience

- [x] Replace Socratic Tutor branding with neutral `AI Study` branding
- [x] Replace Socrates imagery with a neutral AI-study avatar
- [x] Remove participant-facing phase labels
- [x] Add a visible `Thinking...` state while the model responds
- [ ] Remove or hide `Switch participant` from the participant-facing UI
- [ ] Keep dev/test controls available only in development
- [ ] Finish the real countdown timer
- [ ] Check all participant-facing copy for internal terminology
- [ ] Confirm the interface stays visually identical across study conditions

## 9. Professor / External Tester Access Debugging

- [ ] Reproduce why Dr. Hashemi was unable to get the tutor working
- [ ] Identify exactly where his flow failed
  - [ ] Participant-code authentication
  - [ ] `/auth/me` restore
  - [ ] Active `study_participation` lookup
  - [ ] Assessment start/resume
  - [ ] Tutor session start
  - [ ] Model/API response
  - [ ] Frontend/browser issue
- [ ] Verify his test participant code still has a valid active study participation
- [ ] Verify the seeded assignment has the correct round, condition, instruments, and scenarios
- [ ] Test the same code in a clean/incognito browser session
- [ ] Test refresh/re-entry behavior
- [ ] Confirm failures return useful UI messages instead of raw backend errors
- [ ] Capture browser console + backend logs for any reproduced failure
- [ ] Retest from a machine/browser other than the development laptop before declaring the flow ready
- [ ] Have at least one professor/tester successfully complete the full participant flow without developer intervention

## 10. End-to-End Validation and IRB Screenshots

- [ ] Test one Round 1 participant end-to-end
- [ ] Test one Round 2 participant end-to-end
- [ ] Test each AI condition end-to-end
- [ ] Test refresh/re-entry at each major step
- [ ] Verify no duplicate assessment attempts are created
- [ ] Verify condition routing and logging are correct
- [ ] Verify demographics and survey are stored once
- [ ] Capture final screenshots
  - [ ] Participant entry
  - [ ] Demographics
  - [ ] Pretest
  - [ ] AI Study interaction
  - [ ] `Thinking...` state
  - [ ] Timer
  - [ ] Posttest
  - [ ] Final survey
  - [ ] Completion screen

## Near-Term Priority

1. Check in the current UI, assessment, and RPC fixes.
2. Reproduce and fix Dr. Hashemi's access/tutor failure.
3. Make the flow round-aware.
4. Clean up condition codes and condition-based tutor routing.
5. Implement the second/control condition once research-team direction is finalized.
6. Add Round 1 demographics and persistence.
7. Add Round 2 final survey and persistence.
8. Finish the countdown timer and on-task guardrails.
9. Run full external-tester validation.
10. Capture the final IRB screenshots.
