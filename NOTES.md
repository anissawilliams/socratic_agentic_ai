# Socratic Tutor - Next Work Session

## Current checkpoint

The core tutor workflow has been successfully refactored, tested, and
instrumented with turn-level research logging.

Current graph flow:

START → evaluate_response → select_phase → generate_response → log_event → END

Reflection/completion path:

select_phase → generate_reflection → log_event
             → complete_session → log_event → END

Confirmed working:

- `TutorState` refactor
- `SocraticPhase`
- `ResponseEvaluation` model
- `evaluate_response`
- `select_phase`
- consolidated `generate_response`
- reflection separated from Socratic phases
- unified `log_event` implementation
- Supabase `tutor_events` JSONB persistence
- backend-generated UUID session IDs
- backend-generated UUID turn IDs
- `current_turn_id` carried in tutor state
- student messages persisted in research events
- tutor responses persisted in research events
- current/previous phase persisted
- response evaluation persisted
- frontend no longer owns phase logic
- live React → FastAPI → LangGraph → Supabase path verified
- turn-level Elenchus → Aporia transition verified in Supabase

Example persisted research event now contains:

- `current_phase`
- `previous_phase`
- `student_message`
- `tutor_response`
- `tutor_condition`
- `phase_attempt_count`
- `response_evaluation`
- session/turn identifiers

Current response evaluation remains heuristic:

- short responses and hedge terms are treated as hedging
- richer `ResponseEvaluation` fields exist but are not populated yet

Current tutor responses remain deterministic via `PHASE_CONTENT`.
---



## Start here next session



### 1. Clean up and checkpoint current logging

Before adding anything new:

- remove temporary debug prints:
  - `LOG_EVENT`
  - `BUILDING EVENT DATA`
- verify a live browser event exists in Supabase
- rerun:
  - `python -m scripts.test_graph`
- run one browser interaction
- commit/push if not already done

Expected event types:

- `turn_completed`
- `reflection_generated`
- `session_completed`

Verify the reflection and session-complete paths also write events.

---



### 2. Add LangSmith / LangGraph Studio

Goal: add development tracing without replacing Supabase research logging.

Responsibilities:

- Supabase = durable research/event data
- LangSmith = graph/LLM debugging, traces, latency, prompt inspection, evaluation

Tasks:

- add LangSmith environment variables
- add `langgraph.json`
- install/configure LangGraph CLI if needed
- run the graph in Studio
- verify nodes and state transitions are visible

Do not redesign the graph for LangSmith.

---



### 3. Build the Socratic agent layer

Keep the current architecture:

LangGraph nodes = workflow  
Socratic agents = pedagogical personas  
SocraticPhase = selected pedagogical mode

Create:

app/socratic/agents/

- elenchus.py
- aporia.py
- maieutics.py
- dialectic.py

Each agent should:

- have a literature-grounded system prompt
- receive conversation/state context
- call the shared LLM service
- return a tutor response

`generate_response.py` should dispatch based on `current_phase`.

Do NOT create four phase-specific LangGraph nodes again.

---



### 4. Create shared LLM service + config

Move proven LLM setup from `test_llm.py` into:

- `app/config.py`
- `app/services/llm.py`

Centralize:

- model
- temperature
- prompt/version metadata
- shared client construction

Do not instantiate a new OpenAI/ChatOpenAI client inside each agent.

---



### 5. Replace deterministic `PHASE_CONTENT`

Once one agent is wired successfully:

- start with Elenchus
- run one real turn
- inspect output in LangSmith
- verify Supabase logging still works

Then implement:

- Aporia
- Maieutics
- Dialectic

After all four work, remove deterministic `PHASE_CONTENT` generation from the active workflow.

Keep scripted content only if useful for tests/fixtures.

---



### 6. Upgrade `ResponseEvaluation`

Current model:

- `hedging_detected`
- `response_type`
- `reasoning_present`
- `uncertainty_present`
- `phase_goal_satisfied`
- `reasoning_summary`

Current implementation only populates `hedging_detected`.

Next goal:
use structured LLM evaluation to populate the richer model.

Important:

- `minimal` is not the same as `hedging`
- `"I agree."` should likely be `minimal`, not uncertain
- evaluation should eventually drive phase selection more intelligently

Do not change routing behavior until structured evaluation is tested independently.

---



## Architectural rules to preserve

1. Phase is not a graph node.
2. Agent is not a graph node.
3. Nodes represent workflow operations.
4. Tools represent reusable capabilities.
5. Services represent infrastructure.
6. Backend is the single source of truth for tutoring state.
7. Frontend does not evaluate, route, or generate Socratic content.
8. Supabase research logging and LangSmith tracing serve different purposes.
9. Keep one unified `log_event` implementation.
10. Prefer stable domain concepts over workflow-specific file proliferation.

---



## Likely next commit sequence

1. `complete unified tutor event logging`
2. `add LangSmith development tracing`
3. `add shared LLM service`
4. `add Elenchus LLM agent`
5. `add remaining Socratic agents`
6. `add structured response evaluation`

