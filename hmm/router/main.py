from fastapi import APIRouter, Response

router = APIRouter()


def get_router() -> APIRouter:
    return router


@router.get("/ping")
async def ping():
    return Response("pong")
