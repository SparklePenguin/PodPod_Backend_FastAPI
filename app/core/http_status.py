from enum import IntEnum


class HttpStatus(IntEnum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422

    INTERNAL_SERVER_ERROR = 500

    @property
    def phrase(self):
        return self.name.replace("_", " ").title()
