# Study log

One running record of decisions, changes and incidents during data collection,
newest first. Each entry: date, what happened, why, and whether participants
were affected. Longer write-ups go in their own file in docs/ and are
linked from here.

No codes, student IDs or written answers in this log.

Items marked **(check)** were reconstructed afterwards; confirm the exact date
or value from the database, the codes files or git history.

---

## 2026-11-20 · Primary language question added to demographics

- Optional question 6 in Round 1 demographics: "What is your primary language?" (free text, up to 100 characters).
- Stored in `demographic_response.primary_language` (migration `010`). The `submit_demographics` database function is unchanged; the API saves the answer to the row the function creates.
- Asked from this date only: Germany and later cohorts. Spain and GSU completed demographics earlier and have no answer.
- Change made after GSU Round 2 data collection, to avoid affecting students mid-study. Tested locally with test users before deploying.
- A version in the Round 2 survey was drafted and discarded before deployment (migration `009`, undone by `010`) **(check whether 009 was run)**.

## 2026-11-16 to 2026-11-18 · GSU hotel class Round 2

- 51 of 60 hotel-class students completed Round 2 by 2026-11-18; 6 in progress, 3 not started.
- All 325 Round 2 tutor turns completed; no failed turns.
- GSU invoice class: Round 2 not started as of 2026-11-18 (32 ready; 5 still in Round 1).

## 2026-11-12 to 2026-11-15 · GSU Round 2 enrollment

- Round 2 added for all GSU students with `scripts/add_round_two.py`, same content as Spain: `round2_packaging_painting` (pretest and tutor `packaging_waste`, posttest `historical_painting`). Students keep their Round 1 code and condition.
- Hotel class: 58 + 2 late adds; condition split 29 / 29 for the main roster.
- Invoice class (36 + 1 late add): initially missed, added 2026-11-15.
- Overlap students (in both GSU classes) do Round 2 once, with their hotel-class code. The overlap codes file was not given Round 2.
- Students who had not finished Round 1 were given Round 2 as well; it opens only after Round 1 is complete.

## 2026-11-10 to 2026-11-12 · OpenAI key rotated

- New OpenAI key set in Railway by Saber. Keys checked with `scripts/check_keys.py` (OpenAI, Supabase, LangSmith: pass).
- One test session hit a 401 (old key) during the redeploy. No participant sessions affected **(check: no real sessions with failed turns in that window)**.
- Model and prompts unchanged.

## 2026-11 · LangSmith tracing

- Tracing remains on at the request of the faculty investigators; keep LangSmith listed in the IRB documentation.

## 2026-11-03 (approx.) · GSU Round 1 launch **(check exact dates per cohort)**

- Hotel class (`gsu_2026_fall_a`, `gsu_2026_fall_b`, late adds `gsu_2026_fall_late`): `round1_hotel_support` (pretest and tutor `hotel_promotion`, posttest `customer_support`).
- Invoice class (`gsu_invoice_2026_fall`, late add `gsu_invoice_late`): `round1_invoice_access` (pretest and tutor `invoice_reconciliation`, posttest `employee_system_access`); started a few days after the hotel class.
- Randomization: stratified permuted blocks of 4 per roster; seeds recorded in the private codes files **(copy the seed values here)**.
- Students enrolled in both GSU classes (`gsu_invoice_overlap`, 7 students) kept their hotel-class condition, were not randomized for the invoice class, and are excluded from the invoice-class analysis.
- Assessment form widened from 760px to 1040px before launch.

## 2026-11-02 · GSU pre-launch tutor test

- See [GSU_PRELAUNCH_TEST_11_02_2026.md](GSU_PRELAUNCH_TEST_11_02_2026.md). Tutor sometimes supplies a key computed comparison; no prompt change, to keep the tutor identical across cohorts.

## Spain (policy/IR) **(add dates)**

- Both rounds complete. Round 1: `round1_energy_cooling`; Round 2: `round2_packaging_painting`.
- One student withdrew before randomization and completed the activity for course credit only; excluded from analysis.

---

## Template

```
## YYYY-MM-DD · Short title

- What happened or changed.
- Why.
- Who was affected (cohorts, number of participants), or "test users only".
- Files, migrations or commits involved.
```
