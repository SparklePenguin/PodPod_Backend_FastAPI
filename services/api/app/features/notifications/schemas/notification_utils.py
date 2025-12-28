from .notification_type import NotificationType


def get_notification_main_type(notification_type: str) -> str:
    """
    알림 타입 클래스명을 NotificationType enum 값으로 변환

    Args:
        notification_type: 알림 타입 클래스명 (예: PodNotificationType, FollowNotificationType)

    Returns:
        NotificationType enum 값 (예: POD, FOLLOW)
    """
    type_mapping = {
        "PodNotificationType": NotificationType.POD,
        "PodStatusNotificationType": NotificationType.POD_STATUS,
        "RecommendNotificationType": NotificationType.RECOMMEND,
        "ReviewNotificationType": NotificationType.REVIEW,
        "FollowNotificationType": NotificationType.FOLLOW,
    }
    return type_mapping.get(notification_type, NotificationType.POD).value


def to_upper_camel_case(snake_str: str) -> str:
    """
    UPPER_SNAKE_CASE를 UpperCamelCase로 변환

    Args:
        snake_str: UPPER_SNAKE_CASE 문자열 (예: POD_JOIN_REQUEST)

    Returns:
        UpperCamelCase 문자열 (예: PodJoinRequest)
    """
    components = snake_str.lower().split("_")
    return "".join(x.title() for x in components)
