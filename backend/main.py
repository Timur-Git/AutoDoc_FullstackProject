from fastapi import FastAPI, status
import uvicorn

app = FastAPI(
    title="AIAD"
)

@app.get(
    path="/health-api",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    return {"message": "API is running"}


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="127.0.0.1",
        port=8080,
        log_level="info",
    )