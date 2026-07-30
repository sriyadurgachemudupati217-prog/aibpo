"""Predicts the probability that an open task will finish after its due
date ("delayed").

Trains fresh on each call from the company's own completed-task history
(there's no cross-tenant model — each company's workflows are its own).
This is intentionally simple for Phase 3: no persisted/versioned model,
no scheduled retraining. That's the natural next step (see app/ml/registry.py
placeholder) once data volume justifies the overhead; for now, training
on-the-fly on a few hundred rows is fast enough to run inline.

Falls back to an empirical/heuristic estimate when there isn't enough
labeled history to train XGBoost (or XGBoost isn't installed) — a
missing dependency or a new company with little data should never break
the API, just produce a coarser estimate.
"""
from dataclasses import dataclass

from app.core.logging import logger
from app.models.task import Task, TaskStatus

MIN_TRAINING_SAMPLES = 20
_DEFAULT_BASELINE_PROBABILITY = 0.2
_OVERDUE_PROBABILITY = 0.9


@dataclass
class DelayPrediction:
    task_id: str
    probability: float
    method: str  # "xgboost" | "empirical" | "heuristic"


def _extract_features(task: Task, department_index: dict[str, int]) -> list[float]:
    estimated_hours = task.estimated_hours if task.estimated_hours is not None else -1.0
    department_code = float(department_index.get(task.department or "", -1))
    if task.assigned_at and task.due_at:
        lead_time_days = float((task.due_at - task.assigned_at).days)
    else:
        lead_time_days = -1.0
    return [estimated_hours, department_code, lead_time_days]


def _build_department_index(tasks: list[Task]) -> dict[str, int]:
    departments = sorted({t.department for t in tasks if t.department})
    return {dept: i for i, dept in enumerate(departments)}


def _empirical_rate(tasks: list[Task]) -> tuple[float, dict[str, float], dict[str, float]]:
    """Global / per-department / per-employee historical delay rates,
    computed from tasks where the outcome is known."""
    labeled = [t for t in tasks if t.was_delayed is not None]
    if not labeled:
        return _DEFAULT_BASELINE_PROBABILITY, {}, {}

    global_rate = sum(1 for t in labeled if t.was_delayed) / len(labeled)

    by_department: dict[str, list[bool]] = {}
    by_employee: dict[str, list[bool]] = {}
    for t in labeled:
        if t.department:
            by_department.setdefault(t.department, []).append(bool(t.was_delayed))
        if t.employee_id:
            by_employee.setdefault(str(t.employee_id), []).append(bool(t.was_delayed))

    department_rates = {dept: sum(v) / len(v) for dept, v in by_department.items()}
    employee_rates = {emp: sum(v) / len(v) for emp, v in by_employee.items()}
    return global_rate, department_rates, employee_rates


def _heuristic_probability(task: Task, global_rate: float, department_rates: dict, employee_rates: dict) -> float:
    if task.employee_id and str(task.employee_id) in employee_rates:
        return employee_rates[str(task.employee_id)]
    if task.department and task.department in department_rates:
        return department_rates[task.department]
    if task.is_overdue:
        return _OVERDUE_PROBABILITY
    return global_rate


def predict_delay_probabilities(all_tasks: list[Task]) -> list[DelayPrediction]:
    """Scores every open (not-yet-completed) task with a due date.

    `all_tasks` should be the company's full task set — both completed
    (used as training/empirical labels) and open (what gets scored).
    """
    open_tasks = [t for t in all_tasks if t.status != TaskStatus.COMPLETED and t.due_at is not None]
    if not open_tasks:
        return []

    labeled_tasks = [t for t in all_tasks if t.was_delayed is not None]
    global_rate, department_rates, employee_rates = _empirical_rate(all_tasks)

    predictions = _try_xgboost(all_tasks, open_tasks, labeled_tasks)
    if predictions is not None:
        return predictions

    method = "empirical" if labeled_tasks else "heuristic"
    return [
        DelayPrediction(
            task_id=str(t.id),
            probability=round(_heuristic_probability(t, global_rate, department_rates, employee_rates), 4),
            method=method,
        )
        for t in open_tasks
    ]


def _try_xgboost(
    all_tasks: list[Task], open_tasks: list[Task], labeled_tasks: list[Task]
) -> list[DelayPrediction] | None:
    if len(labeled_tasks) < MIN_TRAINING_SAMPLES:
        return None

    labels = [1 if t.was_delayed else 0 for t in labeled_tasks]
    if len(set(labels)) < 2:
        # XGBoost can't learn from a single-class training set — fall back.
        return None

    try:
        import numpy as np
        from xgboost import XGBClassifier
    except ImportError:
        logger.warning("xgboost not installed — falling back to empirical delay rates")
        return None

    department_index = _build_department_index(all_tasks)
    X_train = np.array([_extract_features(t, department_index) for t in labeled_tasks])
    y_train = np.array(labels)

    model = XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train)

    X_predict = np.array([_extract_features(t, department_index) for t in open_tasks])
    probabilities = model.predict_proba(X_predict)[:, 1]

    return [
        DelayPrediction(task_id=str(t.id), probability=round(float(p), 4), method="xgboost")
        for t, p in zip(open_tasks, probabilities)
    ]
