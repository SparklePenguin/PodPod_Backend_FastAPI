# Notification Types & Google Sheets 연동

## 개요

알림 타입은 앱에서 사용되는 모든 푸시 알림의 정의입니다.
`notifications.json`과 Google Sheets 간의 양방향 동기화를 통해 기획자와 개발자가 협업할 수 있습니다.

## 파일 구조

```
services/api/
├── app/core/notifications/
│   ├── __init__.py             # 모듈 export
│   ├── notifications.json      # 알림 타입 정의 (소스 오브 트루스)
│   └── registry.py             # 알림 타입 로더/레지스트리
├── app/features/notifications/
│   ├── schemas/
│   │   └── notification_schemas.py  # Enum 정의 (하위 호환)
│   └── services/
│       └── fcm_service.py      # FCM 전송 비즈니스 로직
└── scripts/
    └── sync_notification_types_to_sheet.py  # Google Sheets 동기화 스크립트
```

> **Note**: 알림 타입 정의는 `core/notifications/`에 위치합니다.
> 이는 `core/exceptions/`, `core/reminders/`와 동일한 패턴입니다.

## notifications.json 구조

### 도메인별 분류

| 도메인 | 알림 타입 | 설명 |
|--------|-----------|------|
| `pod` | POD_JOIN_REQUEST, POD_REQUEST_APPROVED, ... | 파티 관련 알림 |
| `pod_status` | POD_LIKES_THRESHOLD, POD_VIEWS_THRESHOLD, ... | 파티 상태 알림 |
| `recommend` | SAVED_POD_DEADLINE, SAVED_POD_SPOT_OPENED | 추천/좋아요 알림 |
| `review` | REVIEW_CREATED, REVIEW_REMINDER_DAY, ... | 리뷰 알림 |
| `follow` | FOLLOWED_BY_USER, FOLLOWED_USER_CREATED_POD | 팔로우 알림 |

### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `code` | int | 알림 고유 코드 (도메인별 1000/2000/3000/4000/5000 단위) |
| `message_template` | string | 메시지 템플릿 ([placeholder] 형태) |
| `placeholders` | array | 템플릿에 사용되는 변수 목록 |
| `related_id_key` | string | 관련 ID 키 (pod_id, review_id 등) |
| `notification_type` | string | 알림 메인 타입 (POD, REVIEW, FOLLOW 등) |
| `category` | string | 알림 카테고리 (POD, COMMUNITY) |
| `target` | string | 알림 대상 (owner, members, followers 등) |
| `description_ko` | string | 한국어 설명 |
| `description_en` | string | 영어 설명 |
| `dev_note` | string | 개발 노트/가이드 |

### notification_type 종류

| 타입 | 설명 | 카테고리 |
|------|------|----------|
| `POD` | 파티 관련 알림 | POD |
| `POD_STATUS` | 파티 상태 알림 | POD |
| `RECOMMEND` | 추천/좋아요 알림 | POD |
| `REVIEW` | 리뷰 알림 | COMMUNITY |
| `FOLLOW` | 팔로우 알림 | COMMUNITY |

### target 종류

| 타입 | 설명 |
|------|------|
| `owner` | 파티장만 |
| `requester` | 요청자 |
| `members` | 파티원 |
| `all_members` | 파티장 + 파티원 |
| `existing_members` | 기존 파티원 |
| `all_participants` | 모든 참여자 |
| `participants` | 참여자들 |
| `liked_users` | 좋아요한 사용자들 |
| `followers` | 팔로워들 |
| `followed_user` | 팔로우된 사용자 |
| `non_reviewers` | 리뷰 미작성자 |

## Google Sheets 동기화

### 동기화 방향

```
notifications.json ←→ Google Sheets
       ↑                    ↑
    개발자                기획자
  (코드 추가)        (메시지 수정)
```

1. **개발자**: 새 알림 타입을 `notifications.json`에 추가
2. **동기화 스크립트 실행**: JSON → Sheet 업로드
3. **기획자**: Sheet에서 메시지 템플릿, 설명 등 수정
4. **동기화 스크립트 실행**: Sheet → JSON 다운로드

### 동기화 스크립트 실행

```bash
cd services/api/scripts
python sync_notification_types_to_sheet.py
```

### 필요한 환경변수

Infisical `/google-sheet` 경로에서 자동 로드:

| 환경변수 | 설명 |
|----------|------|
| `NOTIFICATION_SHEETS_ID` | 알림 전용 스프레드시트 ID (없으면 `GOOGLE_SHEETS_ID` 사용) |
| `GOOGLE_SHEETS_CREDENTIALS` | Google 서비스 계정 JSON 문자열 |

### 시트 구조

각 도메인별로 별도 시트가 생성됩니다:

| Column | 필드 |
|--------|------|
| A | Code |
| B | Key |
| C | Message Template |
| D | Placeholders (JSON array) |
| E | Related ID Key |
| F | Notification Type |
| G | Category |
| H | Target |
| I | Description (ko) |
| J | Description (en) |
| K | Dev Note |

## 코드에서 사용하기

### notification registry 사용

```python
from app.core.notifications import (
    get_notification_type_info,
    get_all_notification_keys,
    get_notifications_by_category,
)

# 알림 타입 정보 가져오기
noti = get_notification_type_info("POD_JOIN_REQUEST")
print(noti.message_template)  # [nickname]님이 모임에 참여를 요청했어요...
print(noti.category)          # POD

# 메시지 포맷팅
message = noti.format_message(nickname="홍길동")
print(message)  # 홍길동님이 모임에 참여를 요청했어요. 확인해 보세요!

# 카테고리별 알림 조회
pod_notifications = get_notifications_by_category("POD")
community_notifications = get_notifications_by_category("COMMUNITY")
```

### 기존 Enum과의 관계

기존 `PodNotiSubType`, `FollowNotiSubType` 등의 Enum은 하위 호환성을 위해 유지됩니다.
`fcm_service.py`에서는 기존 Enum을 사용하며, 메시지 템플릿은 Enum의 value에 정의되어 있습니다.

```python
# 기존 방식 (fcm_service.py에서 사용)
from app.features.notifications.schemas import PodNotiSubType

message, data = self._format_message(
    PodNotiSubType.POD_JOIN_REQUEST,
    nickname="홍길동",
    pod_id=123,
)

# 새로운 방식 (권장 - 조회/참조용)
from app.core.notifications import get_notification_type_info

noti = get_notification_type_info("POD_JOIN_REQUEST")
```

## 전체 알림 타입 목록

### POD (파티 알림) - 10개

| Code | Key | 설명 | 대상 |
|------|-----|------|------|
| 1001 | POD_JOIN_REQUEST | 참여 요청 | 파티장 |
| 1002 | POD_REQUEST_APPROVED | 참여 승인 | 요청자 |
| 1003 | POD_REQUEST_REJECTED | 참여 거절 | 요청자 |
| 1004 | POD_NEW_MEMBER | 새 멤버 참여 | 기존 파티원 |
| 1005 | POD_UPDATED | 정보 수정 | 전체 멤버 |
| 1006 | POD_CONFIRMED | 파티 확정 | 파티원 |
| 1007 | POD_CANCELED | 파티 취소 | 파티원 |
| 1008 | POD_START_SOON | 시작 1시간 전 | 전체 참여자 |
| 1009 | POD_LOW_ATTENDANCE | 마감 임박 | 파티장 |
| 1010 | POD_CANCELED_SOON | 취소 임박 | 파티장 |

### POD_STATUS (파티 상태 알림) - 4개

| Code | Key | 설명 | 대상 |
|------|-----|------|------|
| 2001 | POD_LIKES_THRESHOLD | 좋아요 10개 달성 | 파티장 |
| 2002 | POD_VIEWS_THRESHOLD | 조회수 10회 달성 | 파티장 |
| 2003 | POD_COMPLETED | 파티 완료 | 참여자들 |
| 2004 | POD_CAPACITY_FULL | 정원 가득 참 | 파티장 |

### RECOMMEND (추천 알림) - 2개

| Code | Key | 설명 | 대상 |
|------|-----|------|------|
| 3001 | SAVED_POD_DEADLINE | 좋아요 파티 마감 임박 | 좋아요한 사용자 |
| 3002 | SAVED_POD_SPOT_OPENED | 좋아요 파티 자리 생김 | 좋아요한 사용자 |

### REVIEW (리뷰 알림) - 4개

| Code | Key | 설명 | 대상 |
|------|-----|------|------|
| 4001 | REVIEW_CREATED | 리뷰 등록 | 파티장 |
| 4002 | REVIEW_REMINDER_DAY | 1일 후 리뷰 유도 | 참여자들 |
| 4003 | REVIEW_REMINDER_WEEK | 1주일 후 리마인드 | 미작성자 |
| 4004 | REVIEW_OTHERS_CREATED | 다른 참여자 리뷰 작성 | 다른 참여자들 |

### FOLLOW (팔로우 알림) - 2개

| Code | Key | 설명 | 대상 |
|------|-----|------|------|
| 5001 | FOLLOWED_BY_USER | 팔로우됨 | 팔로우된 사용자 |
| 5002 | FOLLOWED_USER_CREATED_POD | 팔로우한 유저 파티 생성 | 팔로워들 |

## 관련 문서

- [에러 코드 & Sheet 연동](./error-and-sheet.md)
- [리마인더 타입 & Sheet 연동](./reminder-and-sheet.md)
