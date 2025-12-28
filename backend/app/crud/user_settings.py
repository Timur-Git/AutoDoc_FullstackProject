from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models import UserSettings


async def create_user_settings(
    session: AsyncSession,
    user_serttings: UserSettings
) -> UserSettings:
    session.add(user_serttings)
    await session.commit()
    await session.refresh(user_serttings)
    return user_serttings


async def get_user_settings_by_id(
    session: AsyncSession,
    user_serttings_id: int
) -> UserSettings | None:
    result = await session.execute(
        select(UserSettings).where(UserSettings.id == user_serttings_id)
    )
    return result.scalar_one_or_none()


async def update_user_settings(
    session: AsyncSession,
    user_serttings_id: int,
    **kwargs
) -> UserSettings | None:
    u_set = await get_user_settings_by_id(session, user_serttings_id)
    if not u_set:
        return None
    
    for key, value in kwargs.items():
        if hasattr(u_set, key):
            setattr(u_set, key, value)
    
    await session.commit()
    await session.refresh(u_set)
    return u_set


async def delete_user_settings(
    session: AsyncSession,
    user_serttings_id: int
) -> bool:
    u_set = await get_user_settings_by_id(session, user_serttings_id)
    if not u_set:
        return False
    
    await session.delete(u_set)
    await session.commit()
    return True