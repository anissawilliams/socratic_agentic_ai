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
        cols = [c for c in ["group", "condition", "primary_language_clean", "open_response", "open_response_2"] if c in self.survey]
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

    def latency(self) -> pd.DataFrame:
        """Seconds from student message to tutor reply, per class, round and condition."""
        t = self.turns[~self.turns["failed"]]
        g = t.groupby(self.KEYS)["latency_s"]
        out = pd.DataFrame({
            "turns": g.size(),
            "median_s": g.median(),
            "p75_s": g.quantile(0.75),
            "p90_s": g.quantile(0.90),
            "max_s": g.max(),
            "over_20s_%": g.apply(lambda s: (s > 20).mean() * 100),
        })
        return out.round(1)

    def session_latency(self) -> pd.DataFrame:
        """One row per tutor session: median and slowest reply, for linking to survey comments."""
        t = self.turns[~self.turns["failed"]]
        return (t.groupby(self.KEYS + ["study_participation_id"])["latency_s"]
                .agg(turns="size", median_s="median", max_s="max").round(1).reset_index())

    def repetition(self, threshold: float = 0.6) -> pd.DataFrame:
        """For each Socratic turn, how similar the tutor's reply is to its earlier replies
        in the same session (cosine similarity of word and two-word TF-IDF, 0 to 1).

        A turn is a near-repeat when its similarity to any earlier reply reaches
        `threshold`. Check a sample of flagged pairs by eye before reporting a threshold.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        t = self.turns[(self.turns["condition"] == "Socratic") & ~self.turns["failed"]]
        t = t.sort_values(["study_participation_id", "turn_number"])
        rows = []
        for pid, conv in t.groupby("study_participation_id"):
            replies = conv["tutor_response"].fillna("").tolist()
            if len(replies) < 2:
                continue
            vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit(replies)
            sim = cosine_similarity(vec.transform(replies))
            for i in range(1, len(replies)):
                j = int(sim[i, :i].argmax())
                rows.append({
                    "group": conv["group"].iloc[0], "round_number": conv["round_number"].iloc[0],
                    "study_participation_id": pid,
                    "turn_number": conv["turn_number"].iloc[i],
                    "most_similar_turn": conv["turn_number"].iloc[j],
                    "similarity": round(float(sim[i, j]), 2),
                    "near_repeat": bool(sim[i, j] >= threshold),
                    "tutor_response": replies[i], "earlier_response": replies[j],
                })
        return pd.DataFrame(rows)

    def repetition_summary(self, threshold: float = 0.6) -> pd.DataFrame:
        """Share of Socratic turns that nearly repeat an earlier reply, and how concentrated
        repeats are: a few looping sessions vs. a little everywhere."""
        r = self.repetition(threshold)
        if r.empty:
            return pd.DataFrame()
        per_session = r.groupby(["group", "round_number", "study_participation_id"])["near_repeat"].sum()
        by = ["group", "round_number"]
        return pd.DataFrame({
            "turns": r.groupby(by).size(),
            "near_repeat_turns_%": r.groupby(by)["near_repeat"].mean().mul(100),
            "median_similarity": r.groupby(by)["similarity"].median(),
            "sessions": per_session.groupby(level=by).size(),
            "sessions_with_any_repeat": per_session.gt(0).groupby(level=by).sum(),
            "sessions_with_3plus": per_session.ge(3).groupby(level=by).sum(),
        }).round(1)

    def topic_runs(self) -> pd.DataFrame:
        """Repetition in meaning rather than wording: for each Socratic session, the longest
        run of consecutive turns the router kept on the same topic (routing_topic_code),
        and how many turns the evaluator said "stay". Needs the routing_decision and
        response_evaluation exports."""
        t = self.turns[(self.turns["condition"] == "Socratic") & ~self.turns["failed"]]
        if "routing_topic_code" not in t:
            return pd.DataFrame()
        t = t.sort_values(["study_participation_id", "turn_number"])
        rows = []
        for pid, conv in t.groupby("study_participation_id"):
            topics = conv["routing_topic_code"].fillna("").tolist()
            longest = run = 1
            for a, b in zip(topics, topics[1:]):
                run = run + 1 if a and a == b else 1
                longest = max(longest, run)
            decision = conv.get("evaluation_decision_code", pd.Series(dtype=str))
            rows.append({
                "group": conv["group"].iloc[0], "round_number": conv["round_number"].iloc[0],
                "study_participation_id": pid, "turns": len(conv),
                "topics": conv["routing_topic_code"].nunique(),
                "longest_same_topic_run": longest,
                "stay_turns": int((decision == "stay").sum()),
            })
        return pd.DataFrame(rows)

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


LANGUAGE_ALIASES = {
    "eng": "English", "english": "English", "en": "English",
    "spanish": "Spanish", "español": "Spanish", "espanol": "Spanish", "castellano": "Spanish",
    "catalan": "Catalan", "català": "Catalan", "inglés": "English", "ingles": "English", "englisch": "English",
    "german": "German", "deutsch": "German", "spanisch": "Spanish",
}


def normalize_language(value) -> str:
    """Tidy free-text language answers: 'english ' -> 'English'. Several languages
    ('English and Spanish', 'English/Spanish') are kept as 'English; Spanish'."""
    import re
    if pd.isna(value) or not str(value).strip():
        return ""
    parts = [p.strip().strip(".").lower() for p in re.split(r"\s*(?:,|/|&|;|\band\b|\by\b|\bund\b)\s*", str(value)) if p.strip()]
    names = [LANGUAGE_ALIASES.get(p, p.title()) for p in parts]
    return "; ".join(dict.fromkeys(names))


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
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data folder not found: {data_dir}")
    if not list(data_dir.glob("export_*.csv")):
        # Exports saved into dated subfolders (e.g. data/2026-11-08/): use the newest one.
        dated = sorted(d for d in data_dir.iterdir() if d.is_dir() and list(d.glob("export_*.csv")))
        if not dated:
            found = ", ".join(sorted(p.name for p in data_dir.iterdir())[:10]) or "nothing"
            raise FileNotFoundError(f"No export_*.csv files in {data_dir} (found: {found})")
        data_dir = dated[-1]
        print(f"Using exports in {data_dir}")

    def read(name: str) -> pd.DataFrame:
        path = data_dir / f"export_{name}.csv"
        if not path.exists() or path.stat().st_size == 0:
            return pd.DataFrame()
        return pd.read_csv(path)

    subjects = read("study_subject")
    participation = read("study_participation")
    for name, table, column in [("study_subject", subjects, "is_test"),
                                ("study_participation", participation, "cohort_code")]:
        if table.empty or column not in table:
            have = ", ".join(sorted(p.name for p in data_dir.glob("*.csv"))) or "no CSV files"
            raise FileNotFoundError(
                f"export_{name}.csv in {data_dir} is missing, empty or has no '{column}' column. "
                f"Files there: {have}")

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
    if "primary_language" in survey:
        survey["primary_language_clean"] = survey["primary_language"].map(normalize_language)
        survey["english_primary"] = survey["primary_language_clean"].str.split("; ").str[0].eq("English")
        survey.loc[survey["primary_language_clean"] == "", "english_primary"] = pd.NA

    demographics = read("demographic_response")
    if not demographics.empty:
        demographics = demographics[demographics["study_subject_id"].isin(real)]
        demographics = tag(demographics)

    return Study(part, sessions, turns, attempts, answers, survey, demographics, unmapped)
