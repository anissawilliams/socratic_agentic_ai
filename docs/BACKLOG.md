# Development backlog

Ordered work after the split PRs (evaluator, skip-reflection, tutor errors, maieutics).
Check items off as they land on `main`.

## Phase A — Truth in docs and session setup

- [x] **A1.** `BACKLOG.md` — this list
- [x] **A2.** README routing diagram matches graph (no wired reflection; session ends at `complete_session`)
- [x] **A3.** Refresh `NOTES.md` checkpoint (LLM agents, no reflection path, maieutics thread)
- [x] **A4.** Map `study_participant.condition` → `TutorCondition` at session start; fail loudly on unknown codes
- [x] **A5.** Document condition code table in `app/services/condition.py` (keep in sync with `sql/002_participant_condition.sql`)

## Phase B — Study arms (condition drives behavior)

- [ ] **B1.** Branch graph or `generate_response` on `tutor_condition` (`direct_chat` / future `scaffolded`) — non-Socratic arms return 501 at session start until done
- [ ] **B2.** Decide final condition codes (see STUDY_DESIGN §6); migration if enum ≠ DB
- [ ] **B3.** Blinding: stop exposing `condition` / phase to client unless UI requires it (STUDY_DESIGN §5)

## Phase C — Routing validity

- [x] **C1.** Populate `ResponseEvaluation` fields already computed in `evaluate_response` (type, bare_assent, word_count, …)
- [ ] **C2.** Phase preconditions in `select_phase` (e.g. maieutics only after concession/minimal at aporia) — design choice from STUDY_DESIGN §1
- [ ] **C3.** Harness: extend `compare_phases.py` or script to flag cross-phase drift
- [ ] **C4.** Human coding subset + compare to heuristic (research instrument validation)

## Phase D — Persistence and ops

- [ ] **D1.** Session store outside process memory (Supabase table or Redis); survive backend restart
- [ ] **D2.** Remove or archive dead reflection wiring; keep `generate_reflection.py` comment-only or delete after team sign-off
- [ ] **D3.** Deployment checklist in `TODO.md` (LangSmith, load test, retention) — execute before launch

## Phase E — Pedagogy polish (ongoing)

- [ ] **E1.** Maieutics — live tuning from pilot transcripts
- [ ] **E2.** Aporia / elenchus / dialectic — same “follow the thread” standard where appropriate
- [ ] **E3.** Equate turn counts across conditions if needed (STUDY_DESIGN §3)

---

**Current focus:** Phase B (condition arms) and Phase C2 (phase preconditions).
