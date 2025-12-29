from .follow_noti_sub_type import FollowNotiSubType
from .notification_type import NotificationType
from .pod_noti_sub_type import PodNotiSubType
from .pod_status_noti_sub_type import PodStatusNotiSubType
from .recommend_noti_sub_type import RecommendNotiSubType
from .review_noti_sub_type import ReviewNotiSubType

# 메인 타입과 서브 타입 매칭
NOTIFICATION_TYPE_MAP = {
    NotificationType.POD: PodNotiSubType,
    NotificationType.POD_STATUS: PodStatusNotiSubType,
    NotificationType.RECOMMEND: RecommendNotiSubType,
    NotificationType.REVIEW: ReviewNotiSubType,
    NotificationType.FOLLOW: FollowNotiSubType,
}
