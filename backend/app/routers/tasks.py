"""Task endpoints: raw task listing plus the Phase 3 analysis views
(workload, bottlenecks, repetitive work, redistribution, delay prediction).
Read-only for all authenticated roles — analysis is informational, not a
mutation, so Employees can see it too (unlike inviting users, which is
Admin/Manager-only)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.task import TaskStatus
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.schemas.task import (
    DelayPredictionRead,
    DepartmentBottleneck,
    RedistributionRecommendation,
    RepetitiveTaskGroup,
    TaskRead,
    WorkloadAnalysis,
)
from app.services.task_analysis_service import TaskAnalysisService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    department: str | None = Query(default=None),
    status: TaskStatus | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskRead]:
    return TaskRepository(db).list_by_company(
        current_user.company_id, department=department, status=status
    )


@router.get("/analysis", response_model=WorkloadAnalysis)
def workload_analysis(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WorkloadAnalysis:
    """Per-employee workload with overloaded/underloaded/balanced flags."""
    return TaskAnalysisService(db).workload_analysis(current_user.company_id)


@router.get("/bottlenecks", response_model=list[DepartmentBottleneck])
def bottlenecks(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[DepartmentBottleneck]:
    """Per-department bottleneck scoring from overdue/blocked ratios and hour overages."""
    return TaskAnalysisService(db).bottlenecks(current_user.company_id)


@router.get("/repetitive", response_model=list[RepetitiveTaskGroup])
def repetitive_work(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RepetitiveTaskGroup]:
    """Repeated (employee, task name) pairs — automation candidates."""
    return TaskAnalysisService(db).repetitive_work(current_user.company_id)


@router.get("/redistribution", response_model=list[RedistributionRecommendation])
def redistribution(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RedistributionRecommendation]:
    """Suggested NOT_STARTED-task moves from overloaded to underloaded employees."""
    return TaskAnalysisService(db).redistribution_recommendations(current_user.company_id)


@router.get("/delay-predictions", response_model=list[DelayPredictionRead])
def delay_predictions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[DelayPredictionRead]:
    """Probability each open task finishes after its due date (XGBoost when
    enough labeled history exists, empirical/heuristic fallback otherwise)."""
    return TaskAnalysisService(db).delay_predictions(current_user.company_id)
