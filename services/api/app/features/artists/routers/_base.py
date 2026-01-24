from fastapi import APIRouter

from app.common.abstract_router import AbstractController


class AritistRootController(AbstractController):
    PREFIX: str = "artists"
    TAG: str = "Artists [BASE]"
    DESCRIPTION: str = "아티스트 관리 API"

    ROUTER = APIRouter(prefix="/artists", tags=[TAG])


class ArtistSchedulerController(AbstractController):
    PREFIX: str = "artists"
    TAG: str = "Artists [SCHEDULES]"
    DESCRIPTION: str = "아티스트 스케쥴 API"

    ROUTER = APIRouter(prefix=f"/{AritistRootController.PREFIX}/schedules", tags=[TAG])


class ArtistSuggestController(AbstractController):
    PREFIX: str = "/artist-suggestions"
    TAG: str = "Artists [SUGGEST]"
    DESCRIPTION: str = "아티스트 스케쥴 API"

    ROUTER = APIRouter(prefix=f"{PREFIX}", tags=[TAG])
