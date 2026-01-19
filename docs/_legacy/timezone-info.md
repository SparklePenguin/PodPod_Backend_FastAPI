# 타임존 처리 가이드

## 개요

이 프로젝트는 모든 날짜/시간을 **UTC** 기준으로 저장하고 처리합니다.

## 저장 방식

### DB 컬럼 타입
```python
# pods 테이블
meeting_date = Column(Date, nullable=False)      # 타임존 정보 없음
meeting_time = Column(Time, nullable=False)      # 타임존 정보 없음
created_at = Column(DateTime, default=...)       # 타임존 정보 없음 (UTC 값 저장)
```

- DB 컬럼 자체는 타임존 정보를 저장하지 않음 (naive datetime)
- 하지만 **저장되는 값은 항상 UTC 기준**

### 클라이언트 → 서버

클라이언트는 UTC ISO 8601 형식으로 전송:
```
2025-01-10T12:00:00Z
2025-01-10T12:00:00+00:00
```

### 입력 검증 (`PodForm`)

서버에서 자동으로 UTC 변환:
```python
@field_validator("meeting_date", mode="before")
def ensure_utc_timezone(cls, v):
    # 타임존 없으면 → UTC로 가정
    # 타임존 있으면 → UTC로 변환
```

| 입력 | 처리 |
|------|------|
| `2025-01-10T12:00:00Z` | UTC로 파싱 |
| `2025-01-10T21:00:00+09:00` | KST → UTC 변환 (12:00 UTC) |
| `2025-01-10T12:00:00` (타임존 없음) | UTC로 가정 |

## 스케줄러 처리

스케줄러에서 시간 비교 시 UTC 사용:
```python
now = datetime.now(timezone.utc)
one_hour_later = now + timedelta(hours=1)

# DB의 meeting_date, meeting_time을 UTC로 해석
meeting_datetime = datetime.combine(
    meeting_date, meeting_time, tzinfo=timezone.utc
)
```

## 응답 직렬화

응답 DTO에서 datetime을 ISO 형식 (Z 포함)으로 변환:
```python
@field_serializer("created_at", "updated_at")
def serialize_datetime(self, dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
```

## 주의사항

1. **DB에 저장된 모든 시간은 UTC**
2. **클라이언트는 UTC로 전송해야 함**
3. **클라이언트에서 표시할 때 로컬 타임존으로 변환**

### 예시: 한국 시간 (KST, UTC+9)

| 한국 시간 | DB 저장값 (UTC) |
|-----------|-----------------|
| 2025-01-10 21:00 KST | 2025-01-10 12:00 UTC |
| 2025-01-11 03:00 KST | 2025-01-10 18:00 UTC |

## 디버깅

스케줄러 로그에서 시간 확인:
```
현재 시간: 2025-01-10 12:00:00+00:00
1시간 후: 2025-01-10 13:00:00+00:00
오늘 날짜: 2025-01-10
```

파티가 알림 대상에 포함되지 않는 경우 확인사항:
1. 파티 status가 RECRUITING인지
2. meeting_date가 오늘(UTC 기준)인지
3. meeting_time이 현재~1시간 후 사이인지
4. 24시간 내 이미 알림을 보냈는지
