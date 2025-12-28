from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Repository(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    github_url: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    repo_name: Mapped[str] = mapped_column(String(100))
    repo_owner: Mapped[str] = mapped_column(String(100))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Отношение "многие-к-одному" с User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="repositories"
    )