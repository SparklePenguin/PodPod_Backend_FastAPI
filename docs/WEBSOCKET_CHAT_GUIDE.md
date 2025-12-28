# WebSocket 채팅 서비스 가이드

## 개요

PodPod 백엔드는 Sendbird와 WebSocket 두 가지 채팅 방식을 지원합니다. Feature Flag를 통해 전환할 수 있습니다.

## 아키텍처

### 모놀리식 구조
- FastAPI 앱과 WebSocket 서비스가 같은 도커 컨테이너에서 실행됩니다
- `ChatService` 추상화 레이어를 통해 Sendbird와 WebSocket을 통합 관리합니다

### 주요 컴포넌트

1. **ChatService** (`app/core/services/chat_service.py`)
   - Sendbird와 WebSocket을 통합하는 추상화 레이어
   - Feature Flag로 자동 전환

2. **WebSocketService** (`app/core/services/websocket_service.py`)
   - WebSocket 연결 관리
   - 채널 및 메시지 관리

3. **WebSocket Router** (`app/features/chat/routers/websocket_router.py`)
   - WebSocket 엔드포인트 제공

## 설정

### Feature Flag 설정

각 환경별 설정 파일에서 `chat.use_websocket` 값을 설정합니다:

```yaml
# config.dev.yaml, config.stg.yaml, config.prod.yaml
chat:
  use_websocket: false  # false: Sendbird 사용, true: WebSocket 사용
```

또는 환경변수로 설정:
```bash
USE_WEBSOCKET_CHAT=true
```

## 사용 방법

### 1. WebSocket 활성화

```yaml
# config.dev.yaml
chat:
  use_websocket: true
```

### 2. 채널 생성

기존 코드는 그대로 사용 가능합니다. `ChatService`가 자동으로 WebSocket을 사용합니다:

```python
from app.core.services.chat_service import ChatService

chat_service = ChatService()
channel = await chat_service.create_group_channel(
    channel_url="pod_123_chat",
    name="파티 채팅방",
    user_ids=["1", "2", "3"],
    data={"pod_id": 123}
)
```

### 3. WebSocket 연결

클라이언트에서 WebSocket 연결:

```javascript
// WebSocket 연결
const token = "your_jwt_token";
const channelUrl = "pod_123_chat";
const ws = new WebSocket(`ws://localhost:8000/api/v1/chat/ws/${channelUrl}?token=${token}`);

// 메시지 수신
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log("받은 메시지:", message);
};

// 메시지 전송
ws.send(JSON.stringify({
    type: "MESG",
    message: "안녕하세요!"
}));
```

### 4. 메시지 형식

#### 전송 형식
```json
{
    "type": "MESG",  // 메시지 타입 (MESG, FILE, IMAGE 등)
    "message": "메시지 내용"
}
```

#### 수신 형식
```json
{
    "type": "MESG",
    "channel_url": "pod_123_chat",
    "user_id": 1,
    "message": "메시지 내용",
    "timestamp": "2024-01-01T00:00:00"
}
```

#### 시스템 메시지
```json
// 사용자 입장
{
    "type": "USER_JOINED",
    "channel_url": "pod_123_chat",
    "user_id": 1,
    "timestamp": "2024-01-01T00:00:00"
}

// 사용자 퇴장
{
    "type": "USER_LEFT",
    "channel_url": "pod_123_chat",
    "user_id": 1
}
```

## API 엔드포인트

### WebSocket 엔드포인트

- **프로덕션**: `ws://your-domain.com/api/v1/chat/ws/{channel_url}?token={jwt_token}`
- **개발**: `ws://localhost:8000/api/v1/chat/ws/{channel_url}?token={jwt_token}`

### 테스트 엔드포인트 (인증 없음)

- `ws://localhost:8000/api/v1/chat/ws/{channel_url}/test?user_id={user_id}`

⚠️ **주의**: 테스트 엔드포인트는 개발 환경에서만 사용하세요.

## 마이그레이션 전략

### 단계별 마이그레이션

1. **Phase 1: 병행 운영**
   - `USE_WEBSOCKET_CHAT=false`로 설정하여 Sendbird 계속 사용
   - WebSocket 기능 테스트 및 검증

2. **Phase 2: 점진적 전환**
   - 특정 채널만 WebSocket 사용 (채널별 Feature Flag 추가 가능)
   - 또는 사용자 그룹별로 전환

3. **Phase 3: 완전 전환**
   - `USE_WEBSOCKET_CHAT=true`로 설정
   - Sendbird 의존성 제거 (선택사항)

### 기존 코드 호환성

기존 `SendbirdService`를 직접 사용하는 코드는 그대로 동작합니다. 
점진적으로 `ChatService`로 마이그레이션할 수 있습니다:

```python
# 기존 코드 (여전히 동작)
from app.core.services.sendbird_service import SendbirdService
sendbird_service = SendbirdService()
channel = await sendbird_service.create_group_channel(...)

# 새로운 코드 (Feature Flag로 자동 전환)
from app.core.services.chat_service import ChatService
chat_service = ChatService()
channel = await chat_service.create_group_channel(...)
```

## 주의사항

1. **메모리 기반 저장**
   - 현재 WebSocket 서비스는 채널 메타데이터를 메모리에만 저장합니다
   - 서버 재시작 시 채널 정보가 초기화됩니다
   - 필요시 DB 연동을 추가할 수 있습니다

2. **스케일링**
   - 단일 서버에서는 정상 동작합니다
   - 여러 서버 인스턴스가 있는 경우, Redis Pub/Sub 등을 사용하여 메시지 동기화가 필요합니다

3. **인증**
   - WebSocket 연결 시 JWT 토큰이 필요합니다
   - 토큰은 Query Parameter로 전달됩니다

## 향후 개선 사항

1. **DB 연동**: 채널 메타데이터를 DB에 저장
2. **Redis Pub/Sub**: 다중 서버 환경 지원
3. **메시지 히스토리**: 메시지 저장 및 조회 기능
4. **파일 전송**: 이미지/파일 전송 지원
5. **읽음 확인**: 메시지 읽음 상태 관리

## 문제 해결

### WebSocket 연결 실패
- JWT 토큰이 유효한지 확인
- 채널이 존재하는지 확인 (`get_channel_metadata` 사용)
- 사용자가 채널 멤버인지 확인

### 메시지가 전송되지 않음
- WebSocket 연결 상태 확인
- 채널 URL이 정확한지 확인
- 서버 로그 확인

### Feature Flag가 작동하지 않음
- 설정 파일의 `chat.use_websocket` 값 확인
- 환경변수 `USE_WEBSOCKET_CHAT` 확인
- 서버 재시작 필요할 수 있음
