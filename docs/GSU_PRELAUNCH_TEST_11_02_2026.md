# Pre-launch tutor test: Georgia State, Round 1

- **Date:** 2026-11-02
- **Tester:** Anissa Williams
- **Environment:** production (live site), test participants only (`is_test = true`)
- **Content:** `round1_hotel_support` 1.0.0 (pretest and tutor: `hotel_promotion`; posttest: `customer_support`); tutor scenario `hotel_promotion` 0.1.0
- **Model and prompts:** unchanged from the Spain cohort (same Socratic prompt bundle, same model and temperature)
- **Decision:** no changes to the tutor for the study

## Purpose

Check, before Georgia State students start, that the new hotel scenario loads in production and that the Socratic evaluator and router behave as intended with it.

## Method

Two Socratic test sessions on production. Scripted student replies covered a weak claim, an evasive answer ("Yeah."), a misreading of the chart, partial and strong insights, a reversal of an earlier position, and "idk".

## Results

| Behavior | Result |
| --- | --- |
| Pushes back on a weak claim ("12% increase, expand everywhere") | Pass |
| Does not advance on an evasive answer | Pass |
| Recognizes real progress and moves to a new angle | Pass |
| Keeps raising the challenge before the 14-minute minimum | Pass |
| Covers the learning objective: comparison group, selection, season, chart axis, spread across hotels, directors' trade-off | Pass |
| Catches a contradiction with the student's earlier position | Pass |
| After "idk", narrows the question without answering it | Pass |
| States conclusions for the student | Did not happen |

## Observation: tutor sometimes supplies a key comparison

When the student signalled being stuck at the very start ("I am not really sure. What do you think?"), the tutor did not give an opinion, but its next question computed the central comparison itself:

> "Participating hotels gained 24 weekly bookings, while the others gained 10 during the same seasonal rise. What might the extra 14-booking increase suggest about the promotion?"

A milder version occurred in the first session, where the tutor raised the comparison hotels' 180 to 190 rise before the student mentioned it.

Comparing the participating hotels with the others is the central reasoning step in the learning objective. The tutor still asks the student to interpret the figure, so this is a strong hint rather than a stated conclusion, but it is more than intended.

Questions that quote scenario facts (the axis starting at 175, six of eight hotels improving, the two directors' positions) are not counted as leaks: the scenario text states them.

## Decision and rationale

The research team decided not to change the tutor prompt for the study:

- The same prompt ran for the Spain cohort, so keeping it holds the tutor constant across cohorts.
- A prompt change the day before launch could not be properly retested.
- The behavior is fully logged and can be measured afterwards.

## Follow-up for analysis

- Measure, from the Socratic transcripts of all cohorts, how often the tutor introduces a key computed figure or comparison before the student does, and how often this follows a "stuck" message.
- Report it as a limitation, and as a design improvement for future versions (for example, instructing the tutor to ask the student to compute or compare rather than doing so itself).

## Other checks in this test

- Production initially lacked the new content because the content commit had not been pushed; resolved by pushing and redeploying.
- Assessment form widened from 760px to 1040px before launch so long scenarios are easier to read. Spain had finished both rounds, and no Georgia State student had started, so every Georgia State student sees the same layout.