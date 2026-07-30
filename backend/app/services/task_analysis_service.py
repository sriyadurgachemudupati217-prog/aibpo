"""Business logic for the four TASK ANALYSIS capabilities:
workload imbalance, bottlenecks, repetitive work, and redistribution
recommendations. Delay prediction lives in app.ml.delay_prediction and is
wired in via `delay_predictions()` below.

All of this operates on a single company's tasks — always scoped by the
resolved current_user.company_id in the router, never a client-supplied id.
"""
import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.ml.delay_prediction.model import predict_delay_probabilities
from app.models.employee import Employee
from app.models.task import Task, TaskStatus
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import (
    DelayPredictionRead,
    DepartmentBottleneck,
    EmployeeWorkload,
    RedistributionRecommendation,
    RepetitiveTaskGroup,
    WorkloadAnalysis,
)

# An employee whose estimated workload exceeds their department's mean by
# this factor is flagged overloaded; below the inverse factor, underloaded.
OVERLOAD_FACTOR = 1.5
UNDERLOAD_FACTOR = 0.5

# A (employee, normalized task name) pair repeated at least this often is
# surfaced as a repetitive-work / automation candidate.
REPETITION_THRESHOLD = 3
AUTOMATION_THRESHOLD = 5


class TaskAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.tasks = TaskRepository(db)
        self.employees = EmployeeRepository(db)

    def _all_tasks(self, company_id: uuid.UUID) -> list[Task]:
        return self.tasks.list_by_company(company_id)

    def _employee_lookup(self, company_id: uuid.UUID) -> dict[str, Employee]:
        return {str(e.id): e for e in self.employees.list_by_company(company_id)}

    # --- Workload imbalance ---

    def workload_analysis(self, company_id: uuid.UUID) -> WorkloadAnalysis:
        tasks = self._all_tasks(company_id)
        employees = self._employee_lookup(company_id)

        per_employee: dict[str, list[Task]] = defaultdict(list)
        for t in tasks:
            if t.employee_id:
                per_employee[str(t.employee_id)].append(t)

        # Department mean estimated-hours-per-employee, used as the imbalance baseline.
        dept_employee_hours: dict[str, list[float]] = defaultdict(list)
        for emp_id, emp_tasks in per_employee.items():
            total_hours = sum(t.estimated_hours or 0.0 for t in emp_tasks)
            employee = employees.get(emp_id)
            if employee and employee.department:
                dept_employee_hours[employee.department].append(total_hours)

        department_mean = {
            dept: (sum(vals) / len(vals) if vals else 0.0) for dept, vals in dept_employee_hours.items()
        }

        results: list[EmployeeWorkload] = []
        for emp_id, emp_tasks in per_employee.items():
            employee = employees.get(emp_id)
            if not employee:
                continue
            total_estimated = sum(t.estimated_hours or 0.0 for t in emp_tasks)
            total_actual = sum(t.actual_hours or 0.0 for t in emp_tasks)
            mean_for_dept = department_mean.get(employee.department or "", 0.0)

            if mean_for_dept > 0:
                index = total_estimated / mean_for_dept
            else:
                index = 1.0  # no department baseline available — treat as balanced

            if index >= OVERLOAD_FACTOR:
                flag = "overloaded"
            elif index <= UNDERLOAD_FACTOR and mean_for_dept > 0:
                flag = "underloaded"
            else:
                flag = "balanced"

            results.append(
                EmployeeWorkload(
                    employee_id=employee.id,
                    display_name=employee.display_name,
                    department=employee.department,
                    task_count=len(emp_tasks),
                    total_estimated_hours=round(total_estimated, 2),
                    total_actual_hours=round(total_actual, 2),
                    workload_index=round(index, 2),
                    flag=flag,
                )
            )

        results.sort(key=lambda r: r.workload_index, reverse=True)
        return WorkloadAnalysis(
            employees=results,
            department_mean_hours={k: round(v, 2) for k, v in department_mean.items()},
        )

    # --- Bottlenecks ---

    def bottlenecks(self, company_id: uuid.UUID) -> list[DepartmentBottleneck]:
        tasks = self._all_tasks(company_id)
        by_department: dict[str, list[Task]] = defaultdict(list)
        for t in tasks:
            if t.department:
                by_department[t.department].append(t)

        results: list[DepartmentBottleneck] = []
        for department, dept_tasks in by_department.items():
            overdue = sum(1 for t in dept_tasks if t.is_overdue)
            blocked = sum(1 for t in dept_tasks if t.status == TaskStatus.BLOCKED)

            overages = [
                (t.actual_hours - t.estimated_hours)
                for t in dept_tasks
                if t.actual_hours is not None and t.estimated_hours is not None
            ]
            avg_overage = sum(overages) / len(overages) if overages else 0.0

            task_count = len(dept_tasks)
            overdue_ratio = overdue / task_count if task_count else 0.0
            blocked_ratio = blocked / task_count if task_count else 0.0
            # Simple weighted score: overdue/blocked ratios matter most, overage hours a
            # smaller factor (capped so one extreme outlier doesn't dominate the score).
            score = (overdue_ratio * 0.5) + (blocked_ratio * 0.4) + (min(max(avg_overage, 0), 10) / 10 * 0.1)

            results.append(
                DepartmentBottleneck(
                    department=department,
                    task_count=task_count,
                    overdue_count=overdue,
                    blocked_count=blocked,
                    avg_hours_overage=round(avg_overage, 2),
                    bottleneck_score=round(score, 3),
                    is_bottleneck=score >= 0.3,
                )
            )

        results.sort(key=lambda r: r.bottleneck_score, reverse=True)
        return results

    # --- Repetitive work ---

    def repetitive_work(self, company_id: uuid.UUID) -> list[RepetitiveTaskGroup]:
        tasks = self._all_tasks(company_id)
        employees = self._employee_lookup(company_id)

        groups: dict[tuple[str, str], list[Task]] = defaultdict(list)
        for t in tasks:
            if not t.employee_id:
                continue
            normalized_name = t.task_name.strip().lower()
            groups[(str(t.employee_id), normalized_name)].append(t)

        results: list[RepetitiveTaskGroup] = []
        for (emp_id, _normalized_name), group_tasks in groups.items():
            if len(group_tasks) < REPETITION_THRESHOLD:
                continue
            employee = employees.get(emp_id)
            if not employee:
                continue
            total_hours = sum(t.actual_hours or t.estimated_hours or 0.0 for t in group_tasks)
            results.append(
                RepetitiveTaskGroup(
                    employee_id=employee.id,
                    display_name=employee.display_name,
                    task_name=group_tasks[0].task_name.strip(),
                    occurrence_count=len(group_tasks),
                    total_hours=round(total_hours, 2),
                    automation_candidate=len(group_tasks) >= AUTOMATION_THRESHOLD,
                )
            )

        results.sort(key=lambda r: r.occurrence_count, reverse=True)
        return results

    # --- Redistribution ---

    def redistribution_recommendations(self, company_id: uuid.UUID) -> list[RedistributionRecommendation]:
        workload = self.workload_analysis(company_id)
        overloaded = [e for e in workload.employees if e.flag == "overloaded"]
        underloaded = [e for e in workload.employees if e.flag == "underloaded"]
        if not overloaded or not underloaded:
            return []

        tasks = self._all_tasks(company_id)
        movable_by_employee: dict[str, list[Task]] = defaultdict(list)
        for t in tasks:
            if t.employee_id and t.status == TaskStatus.NOT_STARTED:
                movable_by_employee[str(t.employee_id)].append(t)

        # Underloaded employees available in the same department, least-loaded first.
        underloaded_by_dept: dict[str, list[EmployeeWorkload]] = defaultdict(list)
        for e in underloaded:
            if e.department:
                underloaded_by_dept[e.department].append(e)
        for dept_list in underloaded_by_dept.values():
            dept_list.sort(key=lambda e: e.workload_index)

        recommendations: list[RedistributionRecommendation] = []
        for over_emp in overloaded:
            if not over_emp.department:
                continue
            candidates = underloaded_by_dept.get(over_emp.department, [])
            if not candidates:
                continue
            target = candidates[0]

            movable_tasks = movable_by_employee.get(str(over_emp.employee_id), [])
            if not movable_tasks:
                continue

            # Move roughly enough NOT_STARTED work to bring the overloaded
            # employee back toward their department's mean, capped so we
            # don't recommend moving every task away from them at once.
            excess_hours = max(
                0.0,
                over_emp.total_estimated_hours - workload.department_mean_hours.get(over_emp.department, 0.0),
            )
            moved_hours = 0.0
            for task in movable_tasks:
                if moved_hours >= excess_hours:
                    break
                recommendations.append(
                    RedistributionRecommendation(
                        task_id=task.id,
                        task_name=task.task_name,
                        estimated_hours=task.estimated_hours,
                        from_employee_id=over_emp.employee_id,
                        from_employee_name=over_emp.display_name,
                        to_employee_id=target.employee_id,
                        to_employee_name=target.display_name,
                        reason=(
                            f"{over_emp.display_name} is at {over_emp.workload_index}x their "
                            f"department's average workload; {target.display_name} is at "
                            f"{target.workload_index}x."
                        ),
                    )
                )
                moved_hours += task.estimated_hours or 0.0

        return recommendations

    # --- Delay prediction ---

    def delay_predictions(self, company_id: uuid.UUID) -> list[DelayPredictionRead]:
        tasks = self._all_tasks(company_id)
        tasks_by_id = {str(t.id): t for t in tasks}

        predictions = predict_delay_probabilities(tasks)

        # Persist the score on each Task row so other views (e.g. a task list)
        # can show it without recomputing.
        for p in predictions:
            task = tasks_by_id.get(p.task_id)
            if task:
                task.delay_probability = p.probability
                self.db.add(task)
        if predictions:
            self.db.commit()

        results = []
        for p in predictions:
            task = tasks_by_id.get(p.task_id)
            if not task:
                continue
            results.append(
                DelayPredictionRead(
                    task_id=task.id,
                    task_name=task.task_name,
                    employee_id=task.employee_id,
                    department=task.department,
                    due_at=task.due_at,
                    probability=p.probability,
                    method=p.method,
                )
            )
        results.sort(key=lambda r: r.probability, reverse=True)
        return results
