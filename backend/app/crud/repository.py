from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models import Repository


async def create_repository(
    session: AsyncSession,
    repository: Repository
) -> Repository:
    # rep = Repository(
        
    # )
    session.add(repository)
    await session.commit()
    await session.refresh(repository)
    return repository


async def get_repository_by_id(
    session: AsyncSession,
    repository_id: int
) -> Repository | None:
    result = await session.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    return result.scalar_one_or_none()


async def update_repository(
    session: AsyncSession,
    repository_id: int,
    **kwargs
) -> Repository | None:
    rep = await get_repository_by_id(session, repository_id)
    if not rep:
        return None
    
    for key, value in kwargs.items():
        if hasattr(rep, key):
            setattr(rep, key, value)
    
    await session.commit()
    await session.refresh(rep)
    return rep


async def delete_repository(
    session: AsyncSession,
    repository_id: int
) -> bool:
    rep = await get_repository_by_id(session, repository_id)
    if not rep:
        return False
    
    await session.delete(rep)
    await session.commit()
    return True