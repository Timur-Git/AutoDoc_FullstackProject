from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from . import Base


class ThemeEnum(str, enum.Enum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class UserSettings(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    
    theme: Mapped[str] = mapped_column(String(10), default=ThemeEnum.DARK)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="settings",
        uselist=False
    )