"""DB access for Task. Every list/aggregate query is scoped by company_id —
see TaskAnalysisService for how these feed workload/bottleneck analysis."""
import uuid

from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Task:
        task = Task(**kwargs)
        self.db.add(task)
        return task

    def bulk_create(self, tasks: list[Task]) -> None:
        self.db.add_all(tasks)

    def list_by_company(
        self,
        company_id: uuid.UUID,
        department: str | None = None,
        status: TaskStatus | None = None,
        employee_id: uuid.UUID | None = None,
    ) -> list[Task]:
        query = self.db.query(Task).filter(Task.company_id == company_id)
        if department:
            query = query.filter(Task.department == department)
        if status:
            query = query.filter(Task.status == status)
        if employee_id:
            query = query.filter(Task.employee_id == employee_id)
        return query.order_by(Task.created_at.desc()).all()

    def get_by_id_for_company(self, task_id: str | uuid.UUID, company_id: uuid.UUID) -> Task | None:
        return self.db.query(Task).filter(Task.id == task_id, Task.company_id == company_id).first()

    def delete_by_upload(self, upload_id: uuid.UUID) -> None:
        """Re-ingestion safety: if the same upload is somehow reprocessed,
        avoid duplicating tasks."""
        self.db.query(Task).filter(Task.upload_id == upload_id).delete()

    def commit(self) -> None:
        self.db.commit()
