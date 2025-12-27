from fastapi import APIRouter, status

router = APIRouter()


@router.get(
    path="/health-api",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    return {"message": "API is running"}
