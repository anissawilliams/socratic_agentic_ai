Socratic Tutor production-readiness checklist
- [x] Create test participant provisioning script
  - generates participant code
  - creates study_participant
  - creates/links study_subject
  - creates study_participation
- [x] Fresh participant authentication
  - participant code accepted
  - incognito login works
  - opening another tab restores to the correct place
- [x] Pretest start
  - fresh Round 1 participant reached pretest
  - one assessment_attempt created
- [x] Pretest submission
  - attempt moved to submitted
  - exactly 4 assessment_answer rows written
  - study_participation.status advanced to tutor
  - started_at populated
  - completed_at correctly remains null
- [ ] Nice-to-have: preserve unfinished pretest answers across refresh
  - currently lost on refresh
  - defer unless we have time
We left off here
- [ ] Test tutor session + logging
  1. Start tutor with the same participant.
  2. Send 1–2 messages.
  3. Verify a tutor_session row exists.
  4. Verify tutor_turn rows exist.
  5. Verify response_evaluation.
  6. Verify routing_decision.
  7. Verify study_event sequence.
  8. Confirm no duplicate session/turns from normal use.
Then:
- [ ] Complete tutor and verify transition to posttest
- [ ] Test posttest submission
  - one posttest attempt
  - exactly 4 answers
  - participation advances appropriately
- [ ] Build demographics
- [ ] Build final survey
- [ ] Implement 10-minute timers
- [ ] Round-aware flow
- [ ] Condition work once research team confirms design
- [ ] External tester
- [ ] 40–60 participant load test
- [ ] DB integrity check
- [ ] Feature freeze + final rehearsal
For the current test participant, your study_participation_id is:
e083b560-1e6d-4e9b-af03-9ce997492eab

---
Notes: 

[] HIGH: Tutor turn latency ~14–21 seconds. All evaluator/router/tutor work currently uses GPT-5.6 Sol. Investigate model/call strategy before concurrency test.
[] HIGH: frontend does not reactively advance from tutor completion to posttest; refresh required

Where we left off
- Full Round 1 backend flow validated: PASS
- Auth / restore: PASS
- Pretest create/submit/persist: PASS
- Tutor session + evaluator/router logging: PASS
- Tutor completion in DB: PASS
- Posttest create/submit/persist: PASS
- Participation reaches complete: PASS
- Research-data logging/provenance/event trail: looks strong
- Professor-facing logging summary: sent
Tomorrow’s prioritized to-do list
1. Fix tutor → posttest frontend transition
   - backend already moves to posttest
   - UI currently requires refresh
2. Fix posttest completion screen
   - submission succeeds
   - frontend currently goes blank
   - needs a clear completion state
3. Build demographics
   - add migration/table
   - Round 1 only
   - persist once
   - route correctly after submission
4. Build final survey
   - ~4 Likert items
   - 1 open-ended qualitative response
   - persist safely
   - participation should only become complete after this submits
5. Implement the three 10-minute timers
   - pretest
   - tutor/intervention
   - posttest
   - persisted start time
   - explicit behavior at 0:00
   - capture elapsed/timeout state
6. Make flow round-aware
   - Round 1 includes demographics
   - Round 2 skips demographics
   - returning participants resume correctly
7. Resolve condition design once the team answers
   - do not rewrite the intervention until they confirm what Wednesday actually uses
8. Address tutor latency
   - currently ~16.7 sec average
   - likely because tutor + evaluator + router all use gpt-5.6-sol
   - optimize only after core flow is stable
9. External tester pass
   - especially Dr. Hashemi
   - clean/incognito browser
   - no developer intervention
10. 40–60 user concurrency test
    - then inspect DB integrity
    - no state leaks
    - no duplicate attempts/sessions/events
Nice-to-have, not blocker
- preserve unfinished assessment answers across refresh
- polish error messages
- dev-only controls cleanup
- application_revision → real production Git SHA/release ID