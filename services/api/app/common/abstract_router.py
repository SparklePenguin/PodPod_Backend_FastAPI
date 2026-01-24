from abc import ABCMeta

from fastapi import APIRouter


class AbstractController(ABCMeta):
    PREFIX: str
    TAG: str
    DESCRIPTION: str
    ROUTER: APIRouter

    @classmethod
    def to_dict(cls):
        return {
            "name": cls.TAG,
            "description": cls.DESCRIPTION
        }
