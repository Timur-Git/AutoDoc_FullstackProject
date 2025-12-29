from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from . import Base


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    EDITOR = "editor"


class User(Base):
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String(20), default=RoleEnum.USER)
    is_logged_on: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Отношение "один-ко-многим" с Repository
    repositories: Mapped[list["Repository"]] = relationship(
        "Repository",
        back_populates="user",
        uselist=True,
        cascade="all, delete-orphan"  # Удалить репозитории при удалении пользователя
    )

    # Отношение один к одному с UserSettings для пользователя
    settings: Mapped["UserSettings"] = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan" # удалить таблицу настроек соответсвующую пользователю
    )