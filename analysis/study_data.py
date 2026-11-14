"""Load the study exports and build the descriptive summary tables.

All filtering rules live here so every notebook and report uses the same ones:
real participants only, minus excluded subjects and excluded cohorts, with
cohorts grouped into the study's class groups.

    from analysis.study_data import load_study
    study = load_study("rosters/output/exports/2026-11-08")
    study.completion()
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------- study rules

CONDITIONS = {"scenario_questioning": "Socratic", "direct_chat": "Control"}
CONDITION_ORDER = ["Control", "Socratic"]

# cohort_code -> class group used in every table. Add new cohorts here.
COHORT_GROUPS = {
    "spain_2026_fall": "Spain (policy/IR)",
    "gsu_2026_fall_a": "GSU hotel",
    "gsu_2026_fall_b": "GSU hotel",
    "gsu_2026_fall_late": "GSU hotel",
    "gsu_invoice_2026_fall": "GSU invoice",
    "gsu_invoice_late": "GSU invoice",
}

# Whole cohorts left out of analysis, with the reason.
EXCLUDED_COHORTS = {
    "gsu_invoice_overlap": "already enrolled in the GSU hotel class; kept same condition; not randomized for this class",
}

# Individual subjects (study_subject.id) left out of analysis, with the reason.
EXCLUDED_SUBJECTS = {
    "96c7145a-3aa1-441e-9308-884b6b7a37fb": "Spain: withdrew before randomization; completed for course credit only",
}

LIKERT_ITEMS = {
    "likert_1": "Helped me understand the material",
    "likert_2": "I felt engaged",
    "likert_3": "Made me think carefully",
    "likert_4": "Encouraged me to explain my reasoning",
    "likert_5": "Made me reconsider my thinking",
    "likert_6": "Confident I could explain it to someone",
}

CONSTRUCTS = ["recommendation", "evidence_reasoning", "counterargument", "uncertainty_revision"]


def _words(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.split().str.len()


def _visible_text(value) -> str:
    """Tutor reply as the student saw it.

    Some replies were stored as the raw model output (a list of reasoning and
    text blocks). Keep only the text blocks.
    """
    import ast
    if pd.isna(value):
        return ""
    text = str(value)
    if text.startswith("[{"):
        try:
            blocks = ast.literal_eval(text)
            return "\n".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        except (ValueError, SyntaxError):
            return text
    return text


def _numbers(text) -> set[str]:
    """Numbers in a text, normalized: '1,000' -> '1000', '12.0' -> '12'."""
    import re
    found = set()
    for raw in re.findall(r"\d[\d,]*(?:\.\d+)?", "" if pd.isna(text) else str(text)):
        value = float(raw.replace(",", ""))
        found.add(str(int(value)) if value.is_integer() else str(value))
    return found


def _scenario_numbers(content_dir: Path) -> dict[str, set[str]]:
    """Numbers in each scenario's text, keyed by scenario_key, from the assessment YAML files."""
    import yaml
    out: dict[str, set[str]] = {}
    for path in sorted((content_dir / "assessments").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for stage in ("pretest", "posttest"):
            part = data.get(stage) or {}
            if part.get("scenario_key"):
                out.setdefault(part["scenario_key"], set()).update(_numbers(part.get("scenario_text", "")))
    return out


def _time(df: pd.DataFrame, *cols: str) -> pd.DataFrame:
    for col in cols:
        if col in df:
            df[col] = pd.to_datetime(df[col], utc=True, format="ISO8601", errors="coerce")
    return df


def _truthy(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "t", "1"])


# ---------------------------------------------------------------- loading


@dataclass
class Study:
    participation: pd.DataFrame
    sessions: pd.DataFrame
    turns: pd.DataFrame
    attempts: pd.DataFrame
    answers: pd.DataFrame
    survey: pd.DataFrame
    demographics: pd.DataFrame
    unmapped_cohorts: list[str]

    KEYS = ["group", "round_number", "condition"]

    # ---------------------------------------------------------- summaries

    def completion(self) -> pd.DataFrame:
        """Students per class group, round and condition, by status."""
        table = pd.crosstab(
            [self.participation["group"], self.participation["round_number"], self.participation["condition"]],
            self.participation["status"],
        )
        table["total"] = table.sum(axis=1)
        return table

    def time_on_task(self) -> pd.DataFrame:
        done = self.participation.dropna(subset=["total_min"])
        return done.groupby(self.KEYS)["total_min"].agg(["count", "mean", "median", "min", "max"]).round(1)

    def interaction(self) -> pd.DataFrame:
        """AI interaction per class group, round and condition."""
        t = self.turns
        per_student = t.groupby(self.KEYS + ["study_participation_id"]).agg(
            turns=("id", "count"), student_words_total=("student_words", "sum")
        ).reset_index()
        g = self.KEYS
        out = pd.concat([
            self.sessions.groupby(g)["session_min"].mean().rename("session_min_mean"),
            per_student.groupby(g)["turns"].mean().rename("turns_mean"),
            t.groupby(g)["student_words"].median().rename("student_words_per_turn_med"),
            per_student.groupby(g)["student_words_total"].median().rename("student_words_total_med"),
            t.groupby(g)["ai_words"].median().rename("ai_words_per_turn_med"),
            t.groupby(g)["latency_s"].median().rename("latency_med_s"),
            t.groupby(g)["latency_s"].quantile(0.9).rename("latency_p90_s"),
            t.groupby(g)["failed"].sum().rename("failed_turns"),
        ], axis=1)
        return out.round(1)

    def session_endings(self) -> pd.DataFrame:
        return pd.crosstab(
            [self.sessions["group"], self.sessions["round_number"], self.sessions["condition"]],
            self.sessions["end_reason_code"],
        )

    def assessments(self) -> pd.DataFrame:
        """Timeouts and answer length per stage."""
        a = self.attempts
        return (
            a.groupby(self.KEYS + ["stage"])
            .agg(n=("id", "count"), timeouts=("timed_out", "sum"), words_median=("answer_words", "median"))
            .reindex(["pretest", "posttest"], level="stage")
        )

    def pre_post_change(self) -> pd.DataFrame:
        """Per-student change in total answer words, pretest to posttest.

        Length is only a rough engagement proxy; reasoning quality needs rubric scoring.
        """
        wide = self.attempts.pivot_table(
            index=["study_participation_id"] + self.KEYS, columns="stage", values="answer_words"
        ).reset_index()
        wide = wide.dropna(subset=["pretest", "posttest"])
        wide["change"] = wide["posttest"] - wide["pretest"]
        return wide.groupby(self.KEYS)["change"].agg(["count", "mean", "median"]).round(1)

    def words_by_construct(self) -> pd.DataFrame:
        return self.answers.pivot_table(
            index=["group", "round_number", "stage", "construct_code"],
            columns="condition", values="words", aggfunc="median",
        ).reindex(columns=CONDITION_ORDER)

    def survey_means(self) -> pd.DataFrame:
        if self.survey.empty:
            return pd.DataFrame()
        items = [c for c in LIKERT_ITEMS if c in self.survey]
        means = self.survey.groupby(["group", "condition"])[items].mean().T.rename(index=LIKERT_ITEMS)
        return means.round(2)

    def survey_text(self) -> pd.DataFrame:
        cols = [c for c in ["group", "condition", "open_response", "open_response_2"] if c in self.survey]
        return self.survey[cols].sort_values(["group", "condition"]).reset_index(drop=True)

    def demographics_summary(self) -> pd.DataFrame:
        d = self.demographics
        if d.empty:
            return pd.DataFrame()
        rows = []
        for group, part in d.groupby("group"):
            age = pd.to_numeric(part.get("age"), errors="coerce")
            rows.append({
                "group": group,
                "students": len(part),
                "age_median": age.median(),
                "age_missing": int(age.isna().sum()),
                **{f"gender_{k}": v for k, v in part["gender_code"].value_counts().items()},
                **{f"level_{k}": v for k, v in part.get("academic_level_code", pd.Series(dtype=str)).value_counts().items()},
            })
        return pd.DataFrame(rows).set_index("group").fillna(0)

    def evaluations(self) -> pd.DataFrame:
        """Socratic turns with the evaluator's judgment and the router's next move,
        in conversation order. Empty until the evaluation table is exported."""
        cols = ["group", "round_number", "study_participation_id", "turn_number",
                "student_message", "phase_before_code", "phase_goal_satisfied",
                "evaluation_decision_code", "evaluation_reasoning_summary", "evaluation_evidence",
                "learner_contribution", "addressed_question", "unresolved_issue", "follow_up_target",
                "routing_action_code", "routing_selected_phase_code", "routing_topic_code",
                "routing_move_type_code", "routing_target", "routing_reasoning_summary",
                "phase_after_code", "tutor_response", "session_goal_satisfied"]
        t = self.turns[self.turns["condition"] == "Socratic"]
        return t[[c for c in cols if c in t]].sort_values(["study_participation_id", "turn_number"])

    def evaluation_summary(self) -> pd.DataFrame:
        """How often the evaluator advanced vs held the student, per class and round."""
        e = self.evaluations()
        if "evaluation_decision_code" not in e:
            return pd.DataFrame()
        table = pd.crosstab([e["group"], e["round_number"]], e["evaluation_decision_code"])
        if "phase_goal_satisfied" in e:
            table["phase_goal_met_%"] = (
                e.groupby(["group", "round_number"])["phase_goal_satisfied"]
                .apply(lambda s: _truthy(s).mean() * 100).round(0)
            )
        return table

    def phase_moves(self) -> pd.DataFrame:
        """Phase before -> after for every Socratic turn (works without the evaluation table)."""
        t = self.turns[self.turns["condition"] == "Socratic"]
        return pd.crosstab(t["phase_before_code"].fillna("opening"), t["phase_after_code"].fillna("-"))

    def tutor_supplied_numbers(self, content_dir: str | Path = "content") -> pd.DataFrame:
        """Socratic turns where the tutor states a number that is neither in the
        scenario text nor already written by the student.

        A screen for the habit logged in testing: the tutor computing a key figure
        or comparison (e.g. 2 + 5 = 7, or an extra 14 bookings) before the student
        does. Numbers that appear in the scenario are ignored. Read flagged turns
        before drawing conclusions.
        """
        scenario_numbers = _scenario_numbers(Path(content_dir))
        tutor_key = self.participation.set_index("id")["tutor_scenario_key"]
        t = self.turns[self.turns["condition"] == "Socratic"].sort_values(
            ["study_participation_id", "turn_number"]
        )
        flagged = []
        for pid, conv in t.groupby("study_participation_id"):
            seen: set[str] = set(scenario_numbers.get(tutor_key.get(pid), set()))
            for _, row in conv.iterrows():
                seen |= _numbers(row["student_message"])
                new = sorted(_numbers(row["tutor_response"]) - seen, key=float)
                if new:
                    flagged.append({
                        "group": row["group"], "round_number": row["round_number"],
                        "study_participation_id": pid, "turn_number": row["turn_number"],
                        "numbers_introduced": ", ".join(new), "tutor_response": row["tutor_response"],
                    })
        return pd.DataFrame(flagged)


EXCLUDES_FILE = Path(__file__).parent / "exclude_from_analysis" / "excludes"


# Evaluator/router columns that keep their own name when joined onto turns.
KEEP_NAMES = {"phase_goal_satisfied", "session_goal_satisfied", "learner_contribution",
              "addressed_question", "unresolved_issue", "follow_up_target",
              "session_unresolved_issue", "session_completion_reason"}


def _file_excludes(path: Path) -> set[str]:
    """Ids listed in the excludes file (first column; a 'note' column is optional).

    Use the study_participation_id or study_subject id. The participant_id from
    the codes files is not in the exports, so it cannot be matched.
    """
    if not path.exists():
        return set()
    table = pd.read_csv(path, dtype=str)
    return set(table.iloc[:, 0].dropna().str.strip())


def load_study(data_dir: str | Path, excludes_file: str | Path = EXCLUDES_FILE) -> Study:
    data_dir = Path(data_dir)

    def read(name: str) -> pd.DataFrame:
        path = data_dir / f"export_{name}.csv"
        if not path.exists() or path.stat().st_size == 0:
            return pd.DataFrame()
        return pd.read_csv(path)

    subjects = read("study_subject")
    participation = read("study_participation")

    real = subjects.loc[_truthy(subjects["is_test"]) == False, "id"]  # noqa: E712
    real = real[~real.isin(EXCLUDED_SUBJECTS)]
    part = participation[participation["study_subject_id"].isin(real)].copy()
    part = part[~part["cohort_code"].isin(EXCLUDED_COHORTS)]
    listed = _file_excludes(Path(excludes_file))
    matched = listed & (set(participation["id"]) | set(participation["study_subject_id"]))
    if listed - matched:
        import warnings
        warnings.warn(f"Excludes not found in the exports (use study_participation_id): {sorted(listed - matched)}")
    part = part[~part["id"].isin(listed) & ~part["study_subject_id"].isin(listed)]
    real = real[~real.isin(listed)]
    unmapped = sorted(set(part["cohort_code"]) - set(COHORT_GROUPS))
    part["group"] = part["cohort_code"].map(COHORT_GROUPS).fillna(part["cohort_code"])
    part["condition"] = part["assigned_condition_code"].map(CONDITIONS)
    _time(part, "started_at", "completed_at")
    part["total_min"] = (part["completed_at"] - part["started_at"]).dt.total_seconds() / 60

    info = part.set_index("id")[["group", "round_number", "condition"]]

    def tag(df: pd.DataFrame, key: str = "study_participation_id") -> pd.DataFrame:
        if df.empty:
            return df
        return df.merge(info, left_on=key, right_index=True, how="inner")

    sessions = tag(read("tutor_session"))
    _time(sessions, "started_at", "completed_at")
    sessions["session_min"] = (sessions["completed_at"] - sessions["started_at"]).dt.total_seconds() / 60

    turns = read("tutor_turn").merge(
        sessions[["id", "study_participation_id", "group", "round_number", "condition"]],
        left_on="tutor_session_id", right_on="id", suffixes=("", "_session"),
    )
    turns["tutor_response"] = turns["tutor_response"].map(_visible_text)
    turns["student_words"] = _words(turns["student_message"])
    turns["ai_words"] = _words(turns["tutor_response"])
    turns["latency_s"] = pd.to_numeric(turns["latency_ms"], errors="coerce") / 1000
    turns["failed"] = turns["status"].astype(str) != "completed"

    # Evaluator / router records, one row per Socratic turn, joined onto the turns.
    for path in sorted(data_dir.glob("export_*.csv")):
        name = path.stem.removeprefix("export_")
        if not any(k in name for k in ("evaluation", "routing", "avoid_repeating")) or path.stat().st_size == 0:
            continue
        extra = pd.read_csv(path)
        key = next((c for c in extra.columns if c.endswith("turn_id")), None)
        if key is None:
            continue
        if set(extra.columns) <= {key, "item_order", "content", "id", "created_at"}:
            # List tables (e.g. "avoid repeating" items): several rows per turn.
            # Collapse to one text column per turn so turns are never duplicated.
            items = (extra.sort_values([key, "item_order"]).groupby(key)["content"]
                     .agg(lambda x: " | ".join(x.astype(str))).rename(name))
            turns = turns.merge(items, left_on="id", right_index=True, how="left")
            continue
        if extra[key].duplicated().any():
            raise ValueError(f"{path.name}: more than one row per turn; export the table itself, not a join")
        extra = extra.drop(columns=[c for c in ("id", "created_at") if c in extra])
        # Name the columns by source so evaluator and router fields never collide.
        prefix = "evaluation_" if "evaluation" in name else "routing_"
        extra = extra.rename(columns={
            c: c if c == key or c.startswith(prefix) or c in KEEP_NAMES else prefix + c
            for c in extra.columns
        })
        extra = extra.drop(columns=[c for c in extra.columns if c in turns.columns and c != key])
        turns = turns.merge(extra, left_on="id", right_on=key, how="left").drop(columns=[key])

    attempts = tag(read("assessment_attempt"))
    attempts["timed_out"] = _truthy(attempts["timed_out"])
    answers = read("assessment_answer").merge(
        attempts[["id", "study_participation_id", "stage", "group", "round_number", "condition"]],
        left_on="assessment_attempt_id", right_on="id", suffixes=("", "_attempt"),
    )
    answers["words"] = _words(answers["response_text"])
    attempts["answer_words"] = attempts["id"].map(answers.groupby("assessment_attempt_id")["words"].sum()).fillna(0)

    survey = tag(read("survey_response"))

    demographics = read("demographic_response")
    if not demographics.empty:
        demographics = demographics[demographics["study_subject_id"].isin(real)]
        demographics = tag(demographics)

    return Study(part, sessions, turns, attempts, answers, survey, demographics, unmapped)