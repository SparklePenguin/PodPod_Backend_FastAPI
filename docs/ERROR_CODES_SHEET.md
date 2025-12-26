# Google Sheets 에러 코드 추가 목록

이 문서는 Google Sheets에 추가해야 할 에러 코드 목록입니다.
현재 코드에서 사용 중이지만 아직 Google Sheets에 등록되지 않은 에러 키들입니다.

## Google Sheets 형식

Google Sheets는 다음과 같은 컬럼 구조를 가져야 합니다:

| error_key | code | message_ko | message_en | http_status | dev_note |
|-----------|------|------------|------------|-------------|----------|

## 추가해야 할 에러 코드 (Pods 도메인)

### 1. POD_NOT_FOUND
```
error_key: POD_NOT_FOUND
code: 4041
message_ko: 파티를 찾을 수 없습니다. (ID: {pod_id})
message_en: Pod not found (ID: {pod_id})
http_status: 404
dev_note: Pod with ID {pod_id} does not exist in database
```

### 2. POD_FULL
```
error_key: POD_FULL
code: 4013
message_ko: 파티 정원이 가득 찼습니다. (현재 {current_members}/{max_members}명)
message_en: Pod is full ({current_members}/{max_members} members)
http_status: 400
dev_note: Pod has reached maximum capacity
```

### 3. ALREADY_MEMBER (이미 존재)
```
✅ 이미 error_codes.py에 정의되어 있음
error_key: ALREADY_MEMBER
code: 4012
```

### 4. ALREADY_APPLIED (이미 존재)
```
✅ 이미 error_codes.py에 정의되어 있음
error_key: ALREADY_APPLIED
code: 4011
```

### 5. NOT_POD_HOST
```
error_key: NOT_POD_HOST
code: 4031
message_ko: 파티 호스트만 이 작업을 수행할 수 있습니다.
message_en: Only the pod host can perform this action
http_status: 403
dev_note: User {user_id} is not the host of pod {pod_id}
```

### 6. POD_CLOSED
```
error_key: POD_CLOSED
code: 4014
message_ko: 종료된 파티입니다.
message_en: This pod has been closed
http_status: 400
dev_note: Pod is closed and no longer accepting members
```

### 7. POD_APPLICATION_NOT_FOUND
```
error_key: POD_APPLICATION_NOT_FOUND
code: 4042
message_ko: 파티 신청을 찾을 수 없습니다.
message_en: Pod application not found
http_status: 404
dev_note: Application with ID {application_id} does not exist
```

### 8. INVALID_POD_STATUS
```
error_key: INVALID_POD_STATUS
code: 4015
message_ko: 파티 상태가 올바르지 않습니다. (현재: {current_status}, 필요: {required_status})
message_en: Invalid pod status (current: {current_status}, required: {required_status})
http_status: 400
dev_note: Pod has invalid status for this operation
```

### 9. POD_REVIEW_ALREADY_EXISTS
```
error_key: POD_REVIEW_ALREADY_EXISTS
code: 4016
message_ko: 이미 이 파티에 대한 리뷰를 작성했습니다.
message_en: You have already reviewed this pod
http_status: 400
dev_note: User {user_id} has already reviewed pod {pod_id}
```

### 10. POD_REVIEW_NOT_ALLOWED
```
error_key: POD_REVIEW_NOT_ALLOWED
code: 4032
message_ko: 이 파티에 대한 리뷰를 작성할 수 없습니다. ({reason})
message_en: You are not allowed to review this pod ({reason})
http_status: 403
dev_note: User {user_id} cannot review pod {pod_id}
```

## 에러 코드 체계

현재 사용 중인 에러 코드 체계:
- **1xxx**: 인증/로그인 관련 오류
- **2xxx**: 회원 가입/프로필 관련 오류
- **3xxx**: 결제/정산 관련 오류
- **4xxx**: 데이터/리소스 접근 관련 오류
  - **401x**: 파티 신청 관련 (4011: ALREADY_APPLIED, 4012: ALREADY_MEMBER, 4013: POD_FULL, 4014: POD_CLOSED, 4015: INVALID_POD_STATUS, 4016: POD_REVIEW_ALREADY_EXISTS)
  - **403x**: 권한 관련 (4031: NOT_POD_HOST, 4032: POD_REVIEW_NOT_ALLOWED)
  - **404x**: 리소스 찾을 수 없음 (4041: POD_NOT_FOUND, 4042: POD_APPLICATION_NOT_FOUND)
- **5xxx**: 서버/시스템 관련 오류

## 메시지 포맷팅 규칙

메시지에 `{변수명}` 형태로 플레이스홀더를 사용하면, 코드에서 자동으로 치환됩니다.

### 예시

Google Sheets 등록:
```
message_ko: 파티를 찾을 수 없습니다. (ID: {pod_id})
```

코드에서 사용:
```python
raise PodNotFoundException(pod_id=123)
```

실제 응답:
```json
{
  "messageKo": "파티를 찾을 수 없습니다. (ID: 123)"
}
```

## Google Sheets 업데이트 방법

1. Google Sheets 문서 열기
2. 위의 에러 코드들을 한 줄씩 추가
3. 앱 재시작 또는 24시간 대기 (캐시 만료)
4. 또는 강제 리로드 API 호출 (있다면)

## CSV 임포트용 데이터

```csv
error_key,code,message_ko,message_en,http_status,dev_note
POD_NOT_FOUND,4041,파티를 찾을 수 없습니다. (ID: {pod_id}),Pod not found (ID: {pod_id}),404,Pod with ID {pod_id} does not exist in database
POD_FULL,4013,파티 정원이 가득 찼습니다. (현재 {current_members}/{max_members}명),Pod is full ({current_members}/{max_members} members),400,Pod has reached maximum capacity
NOT_POD_HOST,4031,파티 호스트만 이 작업을 수행할 수 있습니다.,Only the pod host can perform this action,403,User {user_id} is not the host of pod {pod_id}
POD_CLOSED,4014,종료된 파티입니다.,This pod has been closed,400,Pod is closed and no longer accepting members
POD_APPLICATION_NOT_FOUND,4042,파티 신청을 찾을 수 없습니다.,Pod application not found,404,Application with ID {application_id} does not exist
INVALID_POD_STATUS,4015,파티 상태가 올바르지 않습니다. (현재: {current_status} 필요: {required_status}),Invalid pod status (current: {current_status} required: {required_status}),400,Pod has invalid status for this operation
POD_REVIEW_ALREADY_EXISTS,4016,이미 이 파티에 대한 리뷰를 작성했습니다.,You have already reviewed this pod,400,User {user_id} has already reviewed pod {pod_id}
POD_REVIEW_NOT_ALLOWED,4032,이 파티에 대한 리뷰를 작성할 수 없습니다. ({reason}),You are not allowed to review this pod ({reason}),403,User {user_id} cannot review pod {pod_id}
```

## 다른 도메인 에러 추가 시

같은 형식으로 에러 키를 정의하고 이 문서에 추가하세요:

### Users 도메인 예시
```
error_key: USER_NOT_FOUND
code: 2041
message_ko: 사용자를 찾을 수 없습니다. (ID: {user_id})
message_en: User not found (ID: {user_id})
http_status: 404
dev_note: User with ID {user_id} does not exist
```

### Auth 도메인 예시
```
error_key: INVALID_TOKEN
code: 1011
message_ko: 유효하지 않은 토큰입니다.
message_en: Invalid token
http_status: 401
dev_note: Token validation failed
```
