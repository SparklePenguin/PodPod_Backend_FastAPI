# Reminder Types & Google Sheets 연동

## 개요

리마인더 타입은 스케줄러에서 자동으로 발송되는 알림의 정의입니다.
`reminders.json`과 Google Sheets 간의 양방향 동기화를 통해 기획자와 개발자가 협업할 수 있습니다.

## 파일 구조

```
services/api/
├── app/core/reminders/
│   ├── __init__.py             # 모듈 export
│   ├── reminders.json          # 리마인더 타입 정의 (소스 오브 트루스)
│   └── registry.py             # 리마인더 타입 로더/레지스트리
├── app/features/reminders/
│   ├── __init__.py             # core/reminders re-export (하위 호환)
│   └── services/
│       └── reminder_service.py # 스케줄러 리마인더 비즈니스 로직
└── scripts/
    └── sync_reminder_types_to_sheet.py  # Google Sheets 동기화 스크립트
```

> **Note**: 리마인더 타입 정의는 `core/reminders/`에 위치합니다. 
> 이는 `core/exceptions/`와 동일한 패턴으로, cross-cutting concern을 core에서 관리합니다.

## reminders.json 구조

### 도메인별 분류

| 도메인 | 설명 |
|--------|------|
| `review_reminders` | 리뷰 관련 리마인더 (1일/1주일 후 리뷰 유도) |
| `pod_reminders` | 파티 관련 리마인더 (시작 임박, 마감 임박, 취소 임박) |
| `saved_pod_reminders` | 좋아요 파티 관련 리마인더 (마감 임박) |

### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `code` | int | 리마인더 고유 코드 (도메인별 100/200/300 단위) |
| `trigger_hours` | int | 트리거 시간 (시간 단위) |
| `trigger_type` | string | 트리거 조건 (after_pod_completed, before_pod_start 등) |
| `target` | string | 알림 대상 (participants, owner_only, liked_users 등) |
| `message_template` | string | 메시지 템플릿 ([placeholder] 형태) |
| `placeholders` | array | 템플릿에 사용되는 변수 목록 |
| `related_id_key` | string | 관련 ID 키 (pod_id 등) |
| `notification_type` | string | 알림 메인 타입 (POD, REVIEW, RECOMMEND) |
| `notification_value` | string | 알림 서브 타입 (FCM data.value) |
| `category` | string | 알림 카테고리 (POD, COMMUNITY) |
| `duplicate_check_hours` | int | 중복 체크 시간 (시간 단위) |
| `description_ko` | string | 한국어 설명 |
| `description_en` | string | 영어 설명 |
| `dev_note` | string | 개발 노트/가이드 |

### trigger_type 종류

| 타입 | 설명 |
|------|------|
| `after_pod_completed` | 파티 완료 후 N시간 |
| `before_pod_start` | 파티 시작 N시간 전 |
| `before_deadline` | 마감 N시간 전 |
| `before_pod_start_recruiting` | 모집 중인 파티 시작 N시간 전 |

### target 종류

| 타입 | 설명 |
|------|------|
| `participants` | 모든 참여자 |
| `participants_with_owner` | 파티장 포함 모든 참여자 |
| `non_reviewers_except_owner` | 리뷰 미작성 참여자 (파티장 제외) |
| `owner_only` | 파티장만 |
| `liked_users` | 좋아요한 사용자들 |

## Google Sheets 동기화

### 동기화 방향

```
reminders.json ←→ Google Sheets
     ↑                  ↑
  개발자              기획자
 (코드 추가)      (메시지 수정)
```

1. **개발자**: 새 리마인더 타입을 `reminders.json`에 추가
2. **동기화 스크립트 실행**: JSON → Sheet 업로드
3. **기획자**: Sheet에서 메시지 템플릿, 설명 등 수정
4. **동기화 스크립트 실행**: Sheet → JSON 다운로드

### 동기화 스크립트 실행

```bash
python services/api/scripts/sync_reminder_types_to_sheet.py
```

### 필요한 환경변수

Infisical `/google-sheet` 경로에서 자동 로드:

| 환경변수 | 설명 |
|----------|------|
| `REMINDER_SHEETS_ID` | 리마인더 전용 스프레드시트 ID (없으면 `GOOGLE_SHEETS_ID` 사용) |
| `GOOGLE_SHEETS_CREDENTIALS` | Google 서비스 계정 JSON 문자열 |

### 시트 구조

각 도메인별로 별도 시트가 생성됩니다:

| Column | 필드 |
|--------|------|
| A | Code |
| B | Key |
| C | Trigger Hours |
| D | Trigger Type |
| E | Target |
| F | Message Template |
| G | Notification Type |
| H | Notification Value |
| I | Category |
| J | Description (ko) |
| K | Description (en) |
| L | Dev Note |

## 코드에서 사용하기

### reminder_registry 사용

```python
from app.core.reminders import (
    get_reminder_info,
    get_all_reminder_keys,
)

# 리마인더 정보 가져오기
reminder = get_reminder_info("REVIEW_REMINDER_DAY")
print(reminder.message_template)  # 😊 오늘 [party_name] 어떠셨나요?...
print(reminder.trigger_hours)     # 24

# 메시지 포맷팅
message = reminder.format_message(party_name="콘서트 파티")
print(message)  # 😊 오늘 콘서트 파티 어떠셨나요? 소중한 리뷰를 남겨보세요!

# 모든 리마인더 키 목록
keys = get_all_reminder_keys()
print(keys)  # ['REVIEW_REMINDER_DAY', 'REVIEW_REMINDER_WEEK', ...]
```

### ReminderConstants와의 관계

기존 `ReminderConstants` 클래스는 하위 호환성을 위해 유지됩니다.
새로운 리마인더 타입 추가 시에는 `reminders.json`에 추가하는 것을 권장합니다.

```python
# 기존 방식 (하위 호환)
from app.features.reminders.services.reminder_service import ReminderConstants

reminder_type = ReminderConstants.REVIEW_REMINDER_DAY

# 새로운 방식 (권장)
from app.core.reminders import get_reminder_info

reminder = get_reminder_info("REVIEW_REMINDER_DAY")
```

## 새 리마인더 타입 추가 방법

### 1. reminders.json에 정의 추가

```json
{
  "pod_reminders": {
    "NEW_REMINDER_TYPE": {
      "code": 204,
      "trigger_hours": 2,
      "trigger_type": "before_pod_start",
      "target": "participants",
      "message_template": "🔔 [party_name] 모임이 2시간 후 시작돼요!",
      "placeholders": ["party_name"],
      "related_id_key": "pod_id",
      "notification_type": "POD",
      "notification_value": "NEW_REMINDER_TYPE",
      "category": "POD",
      "duplicate_check_hours": 24,
      "description_ko": "파티 시작 2시간 전 알림",
      "description_en": "Reminder 2 hours before pod starts",
      "dev_note": "확정된 파티 참여자에게 전송"
    }
  }
}
```

### 2. notification_schemas.py에 Enum 추가

```python
class PodNotiSubType(Enum):
    # ... 기존 타입들
    NEW_REMINDER_TYPE = (
        "🔔 [party_name] 모임이 2시간 후 시작돼요!",
        ["party_name"],
        "pod_id",
    )
```

### 3. FCMService에 전송 메서드 추가

```python
async def send_new_reminder_type(
    self,
    token: str,
    party_name: str,
    pod_id: int,
    db: AsyncSession | None = None,
    user_id: int | None = None,
) -> bool:
    """새로운 리마인더 알림 전송"""
    body, data = self._format_message(
        PodNotiSubType.NEW_REMINDER_TYPE,
        party_name=party_name,
        pod_id=pod_id,
    )
    return await self.send_notification(...)
```

### 4. ReminderService에 스케줄 로직 추가

```python
async def send_new_reminder(self, db: AsyncSession):
    """새로운 리마인더 전송"""
    # 조건에 맞는 파티 조회
    # 대상 사용자에게 알림 전송
    pass
```

### 5. 동기화 스크립트 실행

```bash
python scripts/sync_reminder_types_to_sheet.py
```

## 관련 문서

- [에러 코드 & Sheet 연동](./error-and-sheet.md)
- [알림 시스템 가이드](./notification-guide.md) (TODO)
