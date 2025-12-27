from sqlalchemy.orm import relationship
from typing import List

from backend.app.database.db import Base, Mapped, mapped_column

class User(Base):
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    
    repositories: Mapped[List["Repository"]] = relationship(
        "Repository", back_populates="user", cascade="all, delete-orphan"
    )