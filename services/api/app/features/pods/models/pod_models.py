"""Pod 관련 모델들"""

from datetime import datetime, timezone
from enum import Enum

from app.core.database import Base
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship


# - MARK: Pod Status Enum
class PodStatus(str, Enum):
    """파티 상태 열거형"""

    RECRUITING = "RECRUITING"  # 모집중
    COMPLETED = "COMPLETED"  # 모집 완료
    CLOSED = "CLOSED"  # 종료
    CANCELED = "CANCELED"  # 취소


# - MARK: Pod Enums
class AccompanySubCategory(str, Enum):
    PRE_RECORDING = "사전 녹화"
    BIRTHDAY_CAFE = "생일 카페"
    CONCERT = "콘서트"
    FAN_MEETING = "팬미팅"
    MEAL_CAFE = "식사/카페"
    VENUE_WAITING = "공연장 대기"
    TRAIN_BUS = "기차/버스"


class GoodsSubCategory(str, Enum):
    EXCHANGE = "굿즈 교환"
    SALE = "굿즈 판매"
    GROUP_PURCHASE = "공동 구매"
    POCA_TRADE = "포카 교환 / 수집"
    GOODS_CLASS = "굿즈 제작 클래스"
    CUSTOMIZING = "굿즈 커스터마이징"
    SHOPPING = "굿즈 쇼핑"


class TourSubCategory(str, Enum):
    CONTENTS = "자컨 투어"
    MUSIC_VIDEO = "뮤비 촬영지 투어"
    CAFE = "팬덤 카페 투어"
    GALLERY = "전시회"
    POP_UP = "팝업 투어"
    FAN_SUPPORT = "팬 서포트 투어"


class EtcSubCategory(str, Enum):
    INFO_SHARE = "정보 공유"
    LISTENING_PARTY = "리스닝 파티"
    MUSIC_VIDEO_WATCHING = "뮤비 감상회"
    OTHER = "기타"


class MainCategory(str, Enum):
    ACCOMPANY = "ACCOMPANY"
    GOODS = "GOODS"
    TOUR = "TOUR"
    ETC = "ETC"


# 메인 카테고리와 서브 카테고리 매칭 맵
CATEGORY_SUBCATEGORY_MAP = {
    MainCategory.ACCOMPANY: AccompanySubCategory,
    MainCategory.GOODS: GoodsSubCategory,
    MainCategory.TOUR: TourSubCategory,
    MainCategory.ETC: EtcSubCategory,
}


def get_subcategories_by_main_category(main_category: str) -> list[str]:
    """
    메인 카테고리에 해당하는 서브 카테고리 이름 목록 반환

    Args:
        main_category: 메인 카테고리 (ACCOMPANY, GOODS, TOUR, ETC)

    Returns:
        서브 카테고리 이름 리스트 (예: ["PRE_RECORDING", "BIRTHDAY_CAFE", ...])
    """
    try:
        main_cat = MainCategory(main_category)
        sub_category_enum = CATEGORY_SUBCATEGORY_MAP.get(main_cat)
        if sub_category_enum:
            return [cat.name for cat in sub_category_enum]
        return []
    except ValueError:
        return []


# - MARK: Pod Model
class Pod(Base):
    __tablename__ = "pods"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    selected_artist_id = Column(
        Integer, ForeignKey("artists.id"), nullable=False, index=True
    )
    chat_room_id = Column(
        Integer,
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="채팅방 ID",
    )
    title = Column(String(100), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    sub_categories = Column(Text, nullable=False)
    capacity = Column(Integer, nullable=False)
    place = Column(String(200), nullable=False)
    meeting_date = Column(Date, nullable=False)
    meeting_time = Column(Time, nullable=False)
    status = Column(SQLEnum(PodStatus), default=PodStatus.RECRUITING, nullable=False)
    is_del = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = relationship("User")
    members = relationship(
        "PodMember", back_populates="pod", cascade="all, delete-orphan"
    )
    ratings = relationship(
        "PodRating", back_populates="pod", cascade="all, delete-orphan"
    )
    views = relationship("PodView", back_populates="pod", cascade="all, delete-orphan")
    detail = relationship(
        "PodDetail",
        uselist=False,
        back_populates="pod",
        cascade="all, delete-orphan",
    )
    images = relationship(
        "PodImage",
        primaryjoin="Pod.id == PodImage.pod_id",
        foreign_keys="[PodImage.pod_id]",
        cascade="all, delete-orphan",
    )
    applications = relationship(
        "Application", back_populates="pod", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "PodReview", back_populates="pod", cascade="all, delete-orphan"
    )
    chat_room = relationship("ChatRoom", foreign_keys=[chat_room_id], uselist=False)


# - MARK: Pod Detail Model
class PodDetail(Base):
    __tablename__ = "pod_details"

    pod_id = Column(
        Integer,
        ForeignKey("pods.id", ondelete="CASCADE"),
        primary_key=True,
    )
    description = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    address = Column(String(300), nullable=False)
    sub_address = Column(String(300), nullable=True)
    x = Column(Float, nullable=True, comment="경도 (longitude)")
    y = Column(Float, nullable=True, comment="위도 (latitude)")

    # relations
    pod = relationship("Pod", back_populates="detail")


# - MARK: Pod Image Model
class PodImage(Base):
    """파티 이미지 테이블"""

    __tablename__ = "pod_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(
        Integer,
        ForeignKey("pod_details.pod_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url = Column(String(500), nullable=False)  # 이미지 URL
    thumbnail_url = Column(String(500), nullable=True)  # 썸네일 URL
    display_order = Column(Integer, nullable=False, default=0)  # 표시 순서
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    pod = relationship(
        "Pod",
        primaryjoin="PodImage.pod_id == Pod.id",
        foreign_keys=[pod_id],
        viewonly=True,
    )
    # 하위 호환성을 위한 pod_detail 관계 (viewonly)
    pod_detail = relationship(
        "PodDetail",
        primaryjoin="PodImage.pod_id == PodDetail.pod_id",
        viewonly=True,
    )


# - MARK: Pod Member Model
class PodMember(Base):
    __tablename__ = "pod_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(Integer, ForeignKey("pods.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="owner")
    message = Column(Text, nullable=True, comment="참여 신청 메시지")
    joined_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="참여 신청 시간",
    )

    pod = relationship("Pod", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("pod_id", "user_id", name="uq_pod_members_pod_user"),
    )


# - MARK: Pod View Model
class PodView(Base):
    """파티 조회수 테이블"""

    __tablename__ = "pod_views"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(Integer, ForeignKey("pods.id"), nullable=False, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # 비로그인 사용자도 조회 가능
    ip_address = Column(String(45), nullable=True)  # IPv6 지원
    user_agent = Column(String(500), nullable=True)  # 브라우저 정보
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    pod = relationship("Pod", back_populates="views")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "pod_id", "user_id", "ip_address", name="uq_pod_views_pod_user_ip"
        ),
    )


# - MARK: Pod Rating Model
class PodRating(Base):
    """파티 평점 테이블"""

    __tablename__ = "pod_ratings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(Integer, ForeignKey("pods.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5점 평점
    review = Column(String(500), nullable=True)  # 리뷰 내용
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    pod = relationship("Pod", back_populates="ratings")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("pod_id", "user_id", name="uq_pod_ratings_pod_user"),
    )
