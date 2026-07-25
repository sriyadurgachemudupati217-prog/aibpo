"""DB access for User/Company. Services call this; routers never touch SQLAlchemy directly."""
import uuid

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: str | uuid.UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def list_by_company(self, company_id: str | uuid.UUID) -> list[User]:
        return self.db.query(User).filter(User.company_id == company_id).order_by(User.created_at).all()

    def create_company(self, name: str, industry: str | None = None) -> Company:
        company = Company(name=name, industry=industry)
        self.db.add(company)
        self.db.flush()  # populate company.id without committing yet
        return company

    def create_user(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        self.db.flush()
        return user

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance) -> None:
        self.db.refresh(instance)
