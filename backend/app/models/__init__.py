"""Import every model here so Alembic's autogenerate sees the full metadata.

As later phases add tasks.py, tickets.py, sales.py, etc., import them below.
"""
from app.models.company import Company  # noqa: F401
from app.models.employee import Employee  # noqa: F401
from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.task import Task, TaskStatus  # noqa: F401
from app.models.upload import FileType, Upload, UploadCategory, UploadStatus  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
