from abc import ABCMeta

class AbstractApiLabel(ABCMeta):
    PREFIX: str
    TAG: str
    DESCRIPTION: str

    @classmethod
    def to_dict(cls):
        return {
            "name": cls.TAG,
            "description": cls.DESCRIPTION
        }
