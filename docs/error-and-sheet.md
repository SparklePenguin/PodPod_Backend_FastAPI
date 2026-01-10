# 에러 코드 동기화 가이드

`errors.json`과 Google Sheets 간 양방향 동기화를 수행하는 스크립트입니다.

## 개요

에러 코드는 `services/api/app/core/errors.json`에서 도메인별로 관리됩니다.
기획/QA 팀과 협업을 위해 Google Sheets와 동기화하여 에러 메시지를 공동 편집할 수 있습니다.

## 동기화 흐름

```
┌─────────────────┐                    ┌─────────────────┐
│  errors.json    │ ←──── 양방향 ────→ │  Google Sheets  │
│  (개발자 관리)   │                    │  (기획/QA 편집)  │
└─────────────────┘                    └─────────────────┘
```

### 동기화 규칙

1. **Sheet → JSON (우선)**
   - Sheet에 있는 내용이 JSON보다 우선
   - 기획팀이 Sheet에서 메시지 수정 시 JSON에 반영됨
   - Sheet에 새 에러 코드 추가 시 JSON에 추가됨

2. **JSON → Sheet**
   - JSON에만 있는 에러 코드는 Sheet에 추가됨
   - 개발자가 새 에러 코드 추가 시 Sheet에 자동 반영

3. **새 도메인**
   - JSON에 새 도메인 추가 시 Sheet 자동 생성
   - 헤더 포함하여 초기화

## 시트 구조

각 도메인별로 별도 시트가 생성됩니다.

| Code | Key | HTTP Status | Message (ko) | Message (en) | 해결 가이드 (dev note) |
|------|-----|-------------|--------------|--------------|----------------------|
| 1001 | INVALID_CREDENTIALS | 401 | 이메일 또는 비밀번호가 올바르지 않습니다. | Invalid email or password. | 로그인 정보 확인 필요 |

### 컬럼 설명

- **Code**: 숫자 에러 코드 (도메인별 범위)
- **Key**: 에러 키 (코드에서 사용하는 상수명)
- **HTTP Status**: HTTP 응답 상태 코드
- **Message (ko)**: 한국어 사용자 메시지
- **Message (en)**: 영어 사용자 메시지
- **해결 가이드**: 개발자용 디버깅 노트

## 도메인별 에러 코드 범위

| 도메인 | 코드 범위 | 설명 |
|--------|----------|------|
| common | 0xxx | 공통 에러 |
| auth | 1xxx | 인증/로그인 |
| oauth | 2xxx | OAuth 연동 |
| users | 3xxx | 사용자 관리 |
| pods | 4xxx | 팟 (파티) |
| artists | 5xxx | 아티스트 |
| tendencies | 6xxx | 성향 테스트 |
| chat | 7xxx | 채팅 |
| follow | 8xxx | 팔로우 |
| notifications | 9xxx | 알림 |
| reports | 10xxx | 신고 |

## 사전 요구사항

### 1. Infisical CLI 설치 및 로그인

```bash
# 설치 (macOS)
brew install infisical/get-cli/infisical

# 로그인
infisical login
```

### 2. Infisical 시크릿 설정

`/google-sheet` 경로에 다음 시크릿 설정:

| 키 | 설명 |
|----|------|
| `GOOGLE_SHEETS_ID` | 스프레드시트 ID (URL에서 추출) |
| `GOOGLE_SHEETS_CREDENTIALS` | Google 서비스 계정 JSON 키 (문자열) |

> 스프레드시트 ID는 URL의 `/d/` 와 `/edit` 사이 문자열입니다.
> 예: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

### 3. Google 서비스 계정 권한

서비스 계정 이메일에 스프레드시트 편집 권한 부여 필요

## 사용법

```bash
cd services/api
python scripts/sync_error_codes_to_sheet.py
```

### 실행 예시

```
==================================================
Google Sheets ↔ errors.json 동기화
==================================================
✓ Infisical 환경변수 로드 완료 (path: /google-sheet)
✓ Google Sheets API 인증 완료
✓ errors.json 로드 완료 (11개 도메인)
✓ 기존 시트: ['common', 'auth', 'oauth', ...]

[common]
  Sheet: 5개, JSON: 5개

[auth]
  Sheet: 8개, JSON: 10개
  ↓ JSON 업데이트: INVALID_CREDENTIALS
  + Sheet에 추가: NEW_AUTH_ERROR

...

✓ errors.json 저장 완료

==================================================
동기화 완료!
==================================================
```

## 워크플로우 예시

### 개발자가 새 에러 코드 추가

1. `errors.json`에 새 에러 코드 추가
2. 스크립트 실행 → Sheet에 자동 추가
3. 커밋 & 푸시

### 기획팀이 메시지 수정

1. 기획팀이 Google Sheets에서 메시지 수정
2. 개발자가 스크립트 실행 → JSON 업데이트
3. 커밋 & 푸시

### 새 도메인 추가

1. `errors.json`에 새 도메인 섹션 추가
2. 스크립트 실행 → 새 시트 자동 생성
3. 커밋 & 푸시

## 파일 구조

```
services/api/
├── app/core/
│   ├── errors.json      # 에러 코드 정의 (도메인별 그룹)
│   └── errors.py        # 에러 코드 로딩 및 조회 함수
└── scripts/
    └── sync_error_codes_to_sheet.py  # 동기화 스크립트
```

## 주의사항

- 동기화 후 `errors.json` 변경 사항 확인 필요
- Sheet의 Code, Key는 수정하지 않는 것을 권장 (메시지만 수정)
- 에러 코드 삭제는 수동으로 양쪽에서 진행 필요
