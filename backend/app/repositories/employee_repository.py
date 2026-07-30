"""DB access for Employee. Scoped by company_id throughout."""
import uuid

from sqlalchemy.orm import Session

from app.models.employee import Employee


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, company_id: uuid.UUID, external_id: str) -> Employee | None:
        return (
            self.db.query(Employee)
            .filter(Employee.company_id == company_id, Employee.external_id == external_id)
            .first()
        )

    def get_or_create(
        self, company_id: uuid.UUID, external_id: str, display_name: str, department: str | None
    ) -> Employee:
        employee = self.get_by_external_id(company_id, external_id)
        if employee:
            # Keep the roster fresh: a later file may have better display name/department.
            if department and not employee.department:
                employee.department = department
            self.db.add(employee)
            return employee

        employee = Employee(
            company_id=company_id,
            external_id=external_id,
            display_name=display_name,
            department=department,
        )
        self.db.add(employee)
        self.db.flush()
        return employee

    def list_by_company(self, company_id: uuid.UUID) -> list[Employee]:
        return self.db.query(Employee).filter(Employee.company_id == company_id).all()

    def commit(self) -> None:
        self.db.commit()
