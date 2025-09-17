"""
Compute evaluation metrics from the current SQLite database and persist results
into the evaluation tables. Optionally compare with a manual baseline if present.

Usage (from repo root):
  python evaluation/compute_evaluation_metrics.py \
      --dataset-name "Current Snapshot" \
      --ai-run-label "AI-Core Snapshot" \
      --engine-type ai_core

Notes:
- If baseline rows exist in table `baseline_assignments` for the same dataset,
  baseline metrics and comparisons will be computed as well.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DB_PATH = Path("data/rota_operations.db")


@dataclass
class Assignment:
    employee_id: str
    patient_id: str
    start_time: Optional[str]
    end_time: Optional[str]
    duration: Optional[int]
    travel_time: Optional[int]


def _parse_time_str(hhmm: Optional[str]) -> Optional[time]:
    if not hhmm:
        return None
    try:
        parts = hhmm.strip().split(":")
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return time(h, m)
    except Exception:
        return None


def load_tables(con: sqlite3.Connection) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    cur = con.cursor()
    cur.execute("SELECT * FROM employees")
    cols_e = [c[0] for c in cur.description]
    employees = [dict(zip(cols_e, r)) for r in cur.fetchall()]

    cur.execute("SELECT * FROM patients")
    cols_p = [c[0] for c in cur.description]
    patients = [dict(zip(cols_p, r)) for r in cur.fetchall()]

    cur.execute("SELECT * FROM assignments")
    cols_a = [c[0] for c in cur.description]
    assignments = [dict(zip(cols_a, r)) for r in cur.fetchall()]
    return employees, patients, assignments


def load_baseline(con: sqlite3.Connection) -> List[Dict]:
    cur = con.cursor()
    try:
        cur.execute("SELECT * FROM baseline_assignments")
    except Exception:
        return []
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _employee_map(employees: List[Dict]) -> Dict[str, Dict]:
    m: Dict[str, Dict] = {}
    for e in employees:
        eid = str(e.get("employee_id") or e.get("EmployeeID") or "").strip()
        if eid:
            m[eid] = e
    return m


def _patient_map(patients: List[Dict]) -> Dict[str, Dict]:
    m: Dict[str, Dict] = {}
    for p in patients:
        pid = str(p.get("patient_id") or p.get("PatientID") or "").strip()
        if pid:
            m[pid] = p
    return m


def _dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def compute_overlap_violations(assignments: List[Dict]) -> int:
    by_emp: Dict[str, List[Tuple[datetime, datetime]]] = defaultdict(list)
    for a in assignments:
        st, en = _dt(a.get("start_time")), _dt(a.get("end_time"))
        eid = a.get("employee_id")
        if eid and st and en:
            by_emp[eid].append((st, en))
    total = 0
    for intervals in by_emp.values():
        intervals.sort(key=lambda x: x[0])
        prev_end: Optional[datetime] = None
        for st, en in intervals:
            if prev_end and st < prev_end:
                total += 1
            prev_end = max(prev_end, en) if prev_end else en
    return total


def compute_on_time_rate(assignments: List[Dict], employees: List[Dict]) -> float:
    emp_map = _employee_map(employees)
    on_time = 0
    total = 0
    for a in assignments:
        eid = a.get("employee_id")
        st, en = _dt(a.get("start_time")), _dt(a.get("end_time"))
        if not (eid and st and en):
            continue
        emp = emp_map.get(eid)
        if not emp:
            continue
        es = _parse_time_str(emp.get("earliest_start") or emp.get("EarliestStart"))
        le = _parse_time_str(emp.get("latest_end") or emp.get("LatestEnd"))
        if not (es and le and es < le):
            continue
        # Compare only time-of-day
        within = (st.time() >= es) and (en.time() <= le) and (en > st)
        total += 1
        if within:
            on_time += 1
    return (on_time / total) if total else 0.0


def _needs_nurse(patient: Dict) -> bool:
    supports = (patient.get("required_support") or patient.get("RequiredSupport") or "").lower()
    return "medicine" in supports


def _language_pref(patient: Dict) -> str:
    pref = (patient.get("language_preference") or patient.get("LanguagePreference") or "").strip()
    return pref or "English"


def compute_accuracy_metrics(assignments: List[Dict], employees: List[Dict], patients: List[Dict]) -> Tuple[float, float]:
    emp_map = _employee_map(employees)
    pat_map = _patient_map(patients)
    total = 0
    qual_ok = 0
    lang_ok = 0
    for a in assignments:
        eid = a.get("employee_id")
        pid = a.get("patient_id")
        if not (eid and pid):
            continue
        emp = emp_map.get(eid)
        pat = pat_map.get(pid)
        if not (emp and pat):
            continue
        total += 1
        # Qualification rule
        if _needs_nurse(pat):
            q = (emp.get("qualification") or emp.get("Qualification") or "").strip().lower()
            if q == "nurse":
                qual_ok += 1
        else:
            qual_ok += 1
        # Language rule
        pref = _language_pref(pat).lower()
        if pref == "english":
            lang_ok += 1
        else:
            langs = (emp.get("language_spoken") or emp.get("LanguageSpoken") or "").lower()
            if pref and pref in langs:
                lang_ok += 1
    return ((qual_ok / total) if total else 0.0, (lang_ok / total) if total else 0.0)


def compute_time_metrics(assignments: List[Dict]) -> Tuple[float, float, float]:
    total = len(assignments)
    sum_travel = 0
    sum_service = 0
    for a in assignments:
        t = a.get("travel_time") or 0
        d = a.get("duration") or 0
        sum_travel += int(t or 0)
        sum_service += int(d or 0)
    avg_travel = (sum_travel / total) if total else 0.0
    avg_service = (sum_service / total) if total else 0.0
    return avg_travel, avg_service, float(sum_travel)


def wilson_ci(p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    denominator = 1 + z * z / n
    center = (p + (z * z) / (2 * n)) / denominator
    margin = z * math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n)) / denominator
    return (max(0.0, center - margin), min(1.0, center + margin))


def two_prop_z_test(p1: float, n1: int, p2: float, n2: int) -> float:
    # Return two-tailed p-value for difference in proportions
    if n1 == 0 or n2 == 0:
        return 1.0
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = abs((p1 - p2) / se)
    # Normal approx tail
    def phi(x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    p = 2 * (1 - phi(z))
    return max(0.0, min(1.0, p))


def cohen_h(p1: float, p2: float) -> float:
    return 2 * (math.asin(math.sqrt(min(1.0, max(0.0, p1)))) - math.asin(math.sqrt(min(1.0, max(0.0, p2)))))


def insert_dataset_and_run(con: sqlite3.Connection, name: str, employees: List[Dict], patients: List[Dict]) -> Tuple[int, int]:
    cur = con.cursor()
    # Infer dates from assignments
    cur.execute("SELECT MIN(DATE(start_time)), MAX(DATE(end_time)) FROM assignments WHERE start_time IS NOT NULL AND end_time IS NOT NULL")
    row = cur.fetchone() or (None, None)
    start_date, end_date = row[0], row[1]
    cur.execute(
        """
        INSERT INTO evaluation_datasets (name, description, num_patients, num_employees, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            "Automatically generated snapshot from current DB",
            len(patients),
            len(employees),
            start_date,
            end_date,
        ),
    )
    dataset_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO evaluation_runs (dataset_id, run_label, engine_type, notes)
        VALUES (?, ?, ?, ?)
        """,
        (
            dataset_id,
            f"AI-Core run {datetime.now().isoformat(timespec='seconds')}",
            "ai_core",
            "Metrics computed from current assignments table",
        ),
    )
    run_id = cur.lastrowid
    con.commit()
    return dataset_id, run_id


def insert_metrics(con: sqlite3.Connection, run_id: int, metrics: Dict[str, Tuple[float, str, Dict]]):
    cur = con.cursor()
    for name, (value, unit, details) in metrics.items():
        cur.execute(
            """
            INSERT OR REPLACE INTO evaluation_metrics (run_id, metric_name, metric_value, unit, details_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, name, float(value), unit, json.dumps(details) if details else None),
        )
    con.commit()


def insert_comparisons(
    con: sqlite3.Connection,
    dataset_id: int,
    baseline_run_id: int,
    ai_run_id: int,
    comparisons: Dict[str, Tuple[float, float]],
):
    cur = con.cursor()
    for name, (baseline_value, ai_value) in comparisons.items():
        diff = ai_value - baseline_value
        denom = baseline_value if baseline_value not in (None, 0) else float("nan")
        if denom and not math.isnan(denom):
            if "travel" in name.lower():
                pct = (baseline_value - ai_value) / denom
            else:
                pct = diff / denom
        else:
            pct = None
        cur.execute(
            """
            INSERT INTO evaluation_comparisons (dataset_id, baseline_run_id, ai_run_id, metric_name, baseline_value, ai_value, difference, pct_improvement)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (dataset_id, baseline_run_id, ai_run_id, name, baseline_value, ai_value, diff, pct),
        )
    con.commit()


def insert_stat_test(
    con: sqlite3.Connection,
    dataset_id: int,
    hypothesis: str,
    test_name: str,
    sample_size: int,
    p_value: float,
    effect_size: Optional[float] = None,
    ci: Optional[Tuple[float, float]] = None,
    alpha: float = 0.05,
    details: Optional[Dict] = None,
):
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO statistical_tests (dataset_id, hypothesis, test_name, sample_size, p_value, effect_size, ci_low, ci_high, alpha, details_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dataset_id,
            hypothesis,
            test_name,
            sample_size,
            p_value,
            effect_size,
            (ci[0] if ci else None),
            (ci[1] if ci else None),
            alpha,
            json.dumps(details) if details else None,
        ),
    )
    con.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_PATH), help="Path to SQLite database")
    parser.add_argument("--dataset-name", default="Current Snapshot", help="Name for evaluation dataset")
    parser.add_argument("--ai-run-label", default="AI-Core Snapshot", help="Run label for AI/Core schedule")
    parser.add_argument("--engine-type", default="ai_core", help="Engine type label for the run")
    args = parser.parse_args()

    con = sqlite3.connect(args.db)

    employees, patients, assignments = load_tables(con)
    if not assignments:
        print("No assignments found; generate schedule first.")
        return

    dataset_id, ai_run_id = insert_dataset_and_run(con, args.dataset_name, employees, patients)

    # Core metrics (AI/Core)
    qual_acc, lang_fit = compute_accuracy_metrics(assignments, employees, patients)
    avg_travel, avg_service, total_travel = compute_time_metrics(assignments)
    overlap = compute_overlap_violations(assignments)
    on_time = compute_on_time_rate(assignments, employees)

    ai_metrics: Dict[str, Tuple[float, str, Dict]] = {
        "qualification_match_accuracy": (qual_acc * 100.0, "%", {}),
        "language_fit_rate": (lang_fit * 100.0, "%", {}),
        "avg_travel_minutes": (avg_travel, "minutes", {}),
        "avg_service_minutes": (avg_service, "minutes", {}),
        "total_travel_minutes": (total_travel, "minutes", {}),
        "on_time_completion_rate": (on_time * 100.0, "%", {}),
        "overlap_violations": (float(overlap), "count", {}),
        "assignments_count": (float(len(assignments)), "count", {}),
    }
    insert_metrics(con, ai_run_id, ai_metrics)

    # Baseline handling (if provided)
    baseline = load_baseline(con)
    if baseline:
        # Create a baseline run record
        cur = con.cursor()
        cur.execute(
            "INSERT INTO evaluation_runs (dataset_id, run_label, engine_type, notes) VALUES (?, ?, ?, ?)",
            (dataset_id, f"Baseline run {datetime.now().isoformat(timespec='seconds')}", "baseline", "Imported manual baseline"),
        )
        baseline_run_id = cur.lastrowid
        con.commit()

        # Compute baseline metrics
        # For accuracy metrics, we attempt to compute similarly if patient/employee join is consistent with IDs
        b_qual_acc, b_lang_fit = compute_accuracy_metrics(baseline, employees, patients)
        b_avg_travel, b_avg_service, b_total_travel = compute_time_metrics(baseline)
        b_overlap = compute_overlap_violations(baseline)
        b_on_time = compute_on_time_rate(baseline, employees)

        baseline_metrics: Dict[str, Tuple[float, str, Dict]] = {
            "qualification_match_accuracy": (b_qual_acc * 100.0, "%", {}),
            "language_fit_rate": (b_lang_fit * 100.0, "%", {}),
            "avg_travel_minutes": (b_avg_travel, "minutes", {}),
            "avg_service_minutes": (b_avg_service, "minutes", {}),
            "total_travel_minutes": (b_total_travel, "minutes", {}),
            "on_time_completion_rate": (b_on_time * 100.0, "%", {}),
            "overlap_violations": (float(b_overlap), "count", {}),
            "assignments_count": (float(len(baseline)), "count", {}),
        }
        insert_metrics(con, baseline_run_id, baseline_metrics)

        # Insert comparisons
        comparisons = {
            "qualification_match_accuracy": (baseline_metrics["qualification_match_accuracy"][0], ai_metrics["qualification_match_accuracy"][0]),
            "language_fit_rate": (baseline_metrics["language_fit_rate"][0], ai_metrics["language_fit_rate"][0]),
            "avg_travel_minutes": (baseline_metrics["avg_travel_minutes"][0], ai_metrics["avg_travel_minutes"][0]),
            "on_time_completion_rate": (baseline_metrics["on_time_completion_rate"][0], ai_metrics["on_time_completion_rate"][0]),
            "overlap_violations": (baseline_metrics["overlap_violations"][0], ai_metrics["overlap_violations"][0]),
        }
        insert_comparisons(con, dataset_id, baseline_run_id, ai_run_id, comparisons)

        # Statistical tests examples
        # Proportions for H1 (qualification) and H3 (on-time)
        q_ci = wilson_ci(qual_acc, len(assignments))
        bq_ci = wilson_ci(b_qual_acc, len(baseline))
        q_p = two_prop_z_test(qual_acc, len(assignments), b_qual_acc, len(baseline))
        insert_stat_test(
            con,
            dataset_id,
            hypothesis="H1: qualification accuracy >= baseline and >= 90%",
            test_name="two-proportion z-test",
            sample_size=(len(assignments) + len(baseline)),
            p_value=q_p,
            effect_size=cohen_h(qual_acc, b_qual_acc),
            ci=q_ci,
            details={"ai_ci": q_ci, "baseline_ci": bq_ci},
        )

        ot_ci = wilson_ci(on_time, len(assignments))
        bot_ci = wilson_ci(b_on_time, len(baseline))
        ot_p = two_prop_z_test(on_time, len(assignments), b_on_time, len(baseline))
        insert_stat_test(
            con,
            dataset_id,
            hypothesis="H3: on-time completion >= baseline and >= 90%",
            test_name="two-proportion z-test",
            sample_size=(len(assignments) + len(baseline)),
            p_value=ot_p,
            effect_size=cohen_h(on_time, b_on_time),
            ci=ot_ci,
            details={"ai_ci": ot_ci, "baseline_ci": bot_ci},
        )

    con.close()
    print("Evaluation metrics computed and saved.")


if __name__ == "__main__":
    main()


