from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.config.settings import settings
from backend.app.models import Base


# Создание асинхронного движка для базы данных
DATABASE_URL = settings.get_database_url()

async_engine: AsyncEngine = create_async_engine(
    url=DATABASE_URL,
    echo=False,               # Логирование SQL запросов
    pool_size=20,             # Размер пула соединений
    max_overflow=0,           # Максимум overflow соединений
    pool_pre_ping=True,       # Проверка соединения перед использованием
)


# Фабрика асинхронных сессий для создания новых сессий
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Объекты остаются живыми после commit
    autoflush=False,         # Отключить
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


# Инициализация БД для создания всех таблиц
async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    await async_engine.dispose()