from fastapi import APIRouter
from .endpoints import users, sessions, oauths, artists, tendencies, surveys

api_router = APIRouter()

# 사용자 관련 라우터
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 세션 관련 라우터
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

# OAuth 관련 라우터
api_router.include_router(oauths.router, prefix="/oauths", tags=["oauths"])

# 아티스트 관련 라우터
api_router.include_router(artists.router, prefix="/artists", tags=["artists"])

# 성향 테스트 관련 라우터
api_router.include_router(tendencies.router, prefix="/tendencies", tags=["tendencies"])

# 설문 관련 라우터
api_router.include_router(surveys.router, prefix="/surveys", tags=["surveys"])
