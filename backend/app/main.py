import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import router
from backend.app.database import init_db, close_db


# Lifespan контекст
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    await init_db()
    print("Database initialized")
    
    yield
    
    # Shutdown
    print("Closing database connection...")
    await close_db()
    print("Database connection closed")


app = FastAPI(
    title="AIAD",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://127.0.0.1:3000",
        "https://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(router=router)


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="127.0.0.1",
        port=8080,
        log_level="info",
    )