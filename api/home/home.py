from fastapi import APIRouter, Depends, Response

from core.fastapi.dependencies import AllowAll, PermissionDependency

home_router = APIRouter()


@home_router.get("/health", dependencies=[Depends(PermissionDependency([AllowAll]))])
async def home():
    return Response(status_code=200)
