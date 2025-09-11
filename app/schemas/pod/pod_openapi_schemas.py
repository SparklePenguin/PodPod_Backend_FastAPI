"""
Pod 관련 OpenAPI 스키마 정의
"""

# 파티 생성 요청 스키마
POD_CREATE_REQUEST_SCHEMA = {
    "requestBody": {
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "example": "함께 영화 보러 가요!",
                        },
                        "description": {
                            "type": "string",
                            "example": "재미있는 영화를 함께 감상해요",
                        },
                        "capacity": {"type": "integer", "example": 4},
                        "place": {"type": "string", "example": "CGV 강남점"},
                        "address": {
                            "type": "string",
                            "example": "서울시 강남구 테헤란로 123",
                        },
                        "subAddress": {"type": "string", "example": "2층 3관"},
                        "meetingDate": {
                            "type": "string",
                            "format": "date",
                            "example": "2025-01-15",
                        },
                        "meetingTime": {
                            "type": "string",
                            "format": "time",
                            "example": "19:00",
                        },
                        "subCategory": {
                            "type": "string",
                            "example": "영화,데이트",
                        },
                        "selectedArtistId": {
                            "type": "integer",
                            "example": 1,
                        },
                        "image": {"type": "string", "format": "binary"},
                        "thumbnail": {"type": "string", "format": "binary"},
                    },
                    "required": [
                        "title",
                        "capacity",
                        "place",
                        "address",
                        "meetingDate",
                        "meetingTime",
                        "subCategory",
                    ],
                }
            }
        }
    }
}
