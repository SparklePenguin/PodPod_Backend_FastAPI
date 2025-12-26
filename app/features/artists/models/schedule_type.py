import enum


class ScheduleType(enum.Enum):
    """스케줄 유형 열거형"""

    GENERAL_CONTENT = 1  # 일반 콘텐츠 (영상, 방송 등)
    MUSIC_RELEASE = 2  # 음원/앨범 발매
    BIRTHDAY = 4  # 생일/기념일
    OTHER_EVENT = 5  # 기타 이벤트
