from fastapi import APIRouter

from app.common.abstract_router import AbstractController


class SessionController(AbstractController):
    PREFIX = "/sessions"
    TAG = "Sessions [BASE]"
    DESCRIPTION = "세션 관리 API (로그인/로그아웃)"

    ROUTER = APIRouter(
        prefix=PREFIX,
        tags=[TAG]
    )
