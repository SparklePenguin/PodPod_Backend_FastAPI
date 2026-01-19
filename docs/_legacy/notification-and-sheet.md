# Notification Events & Google Sheets 연동

## 개요

알림 이벤트는 앱에서 사용되는 모든 푸시 알림의 정의입니다.
Google Sheets가 Source of Truth이며, 동기화 스크립트를 통해 `notifications.json`으로 변환됩니다.

## 데이터 흐름

```
NotificationEvent enum → Google Sheets ↔ notifications.json → 서버 런타임
         ↑                     ↑
      개발자               기획자/개발자
   (이벤트 추가)         (메시지, Meta 등 수정)
```

## 파일 구조

```
services/api/
├── app/
│   ├── core/notifications/           # 런타임 설정 로더
│   │   ├── __init__.py
│   │   ├── notification_registry.py  # JSON 로더 (싱글톤)
│   │   └── notifications.json        # 알림 정의 (시트에서 동기화)
│   └── features/notifications/       # 도메인 로직
│       ├── category.py               # NotificationCategory enum
│       ├── event.py                  # NotificationEvent enum
│       ├── category_map.py           # EVENT_CATEGORY_MAP
│       ├── events/                   # 카테고리별 이벤트 정의
│       ├── payloads/                 # 페이로드 정의
│       ├── models/                   # DB 모델
│       ├── repositories/             # 데이터 접근
│       ├── services/                 # 비즈니스 로직
│       │   └── fcm_service.py        # FCM 전송 로직
│       ├── use_cases/
│       ├── routers/
│       └── schemas/
└── scripts/
    └── sync_notification_types_to_sheet.py  # Google Sheets 동기화
```

## notifications.json 구조

### 카테고리

| 카테고리 | 설명 |
|----------|------|
| `POD` | 파티 관련 알림 |
| `REVIEW` | 리뷰 관련 알림 |
| `USER` | 사용자 관련 알림 (팔로우 등) |
| `SYSTEM` | 시스템 알림 (저장한 파티 등) |

### 필드 설명

| 필드 | Source | 설명 |
|------|--------|------|
| `category` | 코드 | 알림 카테고리 (POD, REVIEW, USER, SYSTEM) |
| `message_template` | 시트 | 메시지 템플릿 ([placeholder] 형태) |
| `placeholders` | 시트(Ref) | 템플릿에 사용되는 변수 목록 |
| `related_id_type` | 시트(Ref) | 관련 ID 타입 (pod_id, user_id, review_id) |
| `meta.is_reminder` | 시트 | 리마인더 여부 |
| `ref` | 시트 | 사용할 Ref 타입 목록 |
| `target` | 시트 | 알림 대상 |
| `description` | 시트 | 설명 |

### 예시

```json
{
  "POD_JOIN_REQUESTED": {
    "category": "POD",
    "message_template": "[nickname]님이 모임에 참여를 요청했어요. 확인해 보세요!",
    "placeholders": ["nickname", "user_id"],
    "related_id_type": "user_id",
    "meta": {
      "is_reminder": false
    },
    "ref": ["UserRef"],
    "target": "파티장",
    "description": "파티 참가 신청 알림"
  }
}
```

## Google Sheets 동기화

### 시트 컬럼 구조

| Column | 필드 | Source |
|--------|------|--------|
| A | Category | 코드 (자동) |
| B | Event | 코드 (자동) |
| C | Meta | 시트 |
| D | Ref | 시트 |
| E | Message Template | 시트 |
| F | Target | 시트 |
| G | Description | 시트 |
| H | Dev Note | 시트 |

### Ref별 사용 가능한 Placeholder

| Ref | Placeholders |
|-----|--------------|
| `PodRef` | `[party_name]`, `[pod_id]` |
| `UserRef` | `[nickname]`, `[user_id]` |
| `ReviewRef` | `[review_id]` |

### 동기화 스크립트 실행

```bash
cd services/api
python scripts/sync_notification_types_to_sheet.py
```

### 출력 예시

```
============================================================
Google Sheets ↔ Notification Events 동기화
============================================================

📋 Ref별 사용 가능한 Placeholder:
   PodRef: [party_name], [pod_id]
   UserRef: [nickname], [user_id]
   ReviewRef: [review_id]

✓ Infisical 환경변수 로드 완료 (path: /google-sheet)
✓ Google Sheets API 인증 완료
✓ 기존 시트: ['정의', 'Notifications']

[Notifications]
  코드에서 22개 이벤트 로드
  시트에서 22개 이벤트 로드
  = 이벤트 목록 변경 없음
✓ notifications.json 저장 완료 (22개 이벤트)

⚠️  구현 필요한 이벤트: 2개
   (Message Template이 비어있음 - 시트에서 채워주세요)
   - NEW_EVENT_1
   - NEW_EVENT_2

============================================================
✅ 동기화 완료! (구현 필요: 2개)
============================================================
```

### 필요한 환경변수

Infisical `/google-sheet` 경로에서 자동 로드:

| 환경변수 | 설명 |
|----------|------|
| `NOTIFICATION_SHEETS_ID` | 알림 전용 스프레드시트 ID |
| `GOOGLE_SHEETS_CREDENTIALS` | Google 서비스 계정 JSON 문자열 |

## 새 이벤트 추가하기

### 1. 코드에 이벤트 추가

```python
# app/features/notifications/event.py
class NotificationEvent(str, Enum):
    # ... 기존 이벤트들
    NEW_EVENT = "NEW_EVENT"  # 새 이벤트 추가
```

### 2. 카테고리 매핑 추가

```python
# app/features/notifications/category_map.py
EVENT_CATEGORY_MAP: dict[NotificationEvent, NotificationCategory] = {
    # ... 기존 매핑들
    NotificationEvent.NEW_EVENT: NotificationCategory.POD,  # 카테고리 지정
}
```

### 3. 동기화 스크립트 실행

```bash
cd services/api
python scripts/sync_notification_types_to_sheet.py
```

→ 시트에 새 이벤트가 빈 행으로 추가됨

### 4. 시트에서 정보 채우기

- **Meta**: `is_reminder` (리마인더인 경우)
- **Ref**: `PodRef`, `UserRef`, `ReviewRef` 중 선택
- **Message Template**: 메시지 템플릿 작성
- **Target**: 알림 대상
- **Description**: 설명
- **Dev Note**: 개발 노트

### 5. 다시 동기화

```bash
python scripts/sync_notification_types_to_sheet.py
```

→ `notifications.json` 업데이트됨

## 코드에서 사용하기

### notification_registry 사용

```python
from app.core.notifications import (
    get_notification_info,
    render_message,
    get_related_id_type,
    is_reminder_event,
)

# 알림 정보 가져오기
info = get_notification_info("POD_JOIN_REQUESTED")
print(info.message_template)  # [nickname]님이 모임에 참여를 요청했어요...
print(info.category)          # NotificationCategory.POD
print(info.is_reminder)       # False

# 메시지 렌더링
message = render_message("POD_JOIN_REQUESTED", nickname="홍길동")
print(message)  # 홍길동님이 모임에 참여를 요청했어요. 확인해 보세요!

# related_id 타입 조회
id_type = get_related_id_type("POD_JOIN_REQUESTED")
print(id_type)  # "user_id"

# 리마인더 여부 확인
is_reminder = is_reminder_event("POD_STARTING_SOON")
print(is_reminder)  # True
```

### FCMService에서 사용

```python
from app.features.notifications.event import NotificationEvent
from app.core.notifications import render_message, get_related_id_type

# FCMService 내부에서 메시지 포맷팅
event = NotificationEvent.POD_JOIN_REQUESTED
message = render_message(event, nickname="홍길동")
related_id_type = get_related_id_type(event)
```

## 관련 문서

- [에러 코드 & Sheet 연동](./error-and-sheet.md)
