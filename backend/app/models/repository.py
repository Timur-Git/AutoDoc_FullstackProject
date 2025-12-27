from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from backend.app.database.db import Base, Mapped, mapped_column


class Repository(Base):
    __tablename__ = "repositories"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    github_url: Mapped[str] = mapped_column(unique=True)
    is_public: Mapped[bool] = mapped_column(default=False)
    
    user: Mapped["User"] = relationship("User", back_populates="repositories")
    # documentation_versions: Mapped[List["DocumentationVersion"]] = relationship(
    #     "DocumentationVersion", back_populates="repository", cascade="all, delete-orphan"
    # )
