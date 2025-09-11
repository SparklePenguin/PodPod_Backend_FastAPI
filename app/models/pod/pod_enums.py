from enum import Enum


# 동행 카테고리
class AccompanySubCategory(str, Enum):
    PRE_RECORDING = "사전 녹화"
    BIRTHDAY_CAFE = "생일 카페"
    CONCERT = "콘서트"
    FAN_MEETING = "팬미팅"
    MEAL_CAFE = "식사/카페"
    VENUE_WAITING = "공연장 대기"
    TRAIN_BUS = "기차/버스"


# 굿즈 서브 카테고리
class GoodsSubCategory(str, Enum):
    EXCHANGE = "굿즈 교환"
    SALE = "굿즈 판매"
    GROUP_PURCHASE = "공동 구매"
    POCA_TRADE = "포카 교환 / 수집"
    GOODS_CLASS = "굿즈 제작 클래스"
    CUSTOMIZING = "굿즈 커스터마이징"
    SHOPPING = "굿즈 쇼핑"


# 투어 서브 카테고리
class TourSubCategory(str, Enum):
    CONTENTS = "자컨 투어"
    MUSIC_VIDEO = "뮤비 촬영지 투어"
    CAFE = "팬덤 카페 투어"
    GALLERY = "전시회"
    POP_UP = "팝업 투어"
    FAN_SUPPORT = "팬 서포트 투어"


# ETC 서브 카테고리
class EtcSubCategory(str, Enum):
    INFO_SHARE = "정보 공유"
    LISTENING_PARTY = "리스닝 파티"
    MUSIC_VIDEO_WATCHING = "뮤비 감상회"
    OTHER = "기타"


# 메인 카테고리
class MainCategory(str, Enum):
    ACCOMPANY = "동행"
    GOODS = "굿즈"
    TOUR = "투어"
    ETC = "ETC"
