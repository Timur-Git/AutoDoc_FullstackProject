from pydantic import BaseModel

from backend.app.models import ThemeEnum


class ThemeRequest(BaseModel):
    theme: ThemeEnum

class SettingsResponse(BaseModel):
    theme: ThemeEnum
