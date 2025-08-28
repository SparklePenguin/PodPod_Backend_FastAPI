from fastapi import APIRouter
from .endpoints import users, sessions, oauths

api_router = APIRouter()

# 사용자 관련 라우터
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 세션 관련 라우터
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

# OAuth 관련 라우터
api_router.include_router(oauths.router, prefix="/oauths", tags=["oauths"])
