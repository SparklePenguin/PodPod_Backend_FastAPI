# Config 파일 가이드

## 파일 구조

```
config.dev.yaml   # 개발 환경
config.stg.yaml   # 스테이징 환경
config.prod.yaml  # 프로덕션 환경
```

## 주요 설정 항목

### Environment
```yaml
environment: "development"  # local, development, staging, production
```

### Database
```yaml
database:
  host: "localhost"
  port: 3306
  name: "podpod_dev"
  user: "root"
  # password는 환경 변수 (MYSQL_PASSWORD)
```

### App
```yaml
app:
  name: "PodPod API (Dev)"
  version: "1.0.0"
  base_url: "http://localhost:8000"  # OAuth 리다이렉트 URL 생성에 사용
  root_path: ""  # Nginx 프록시 경로 (예: /stg)
```

**환경별 base_url 예시:**
- **dev**: `http://localhost:8000`
- **staging**: `https://sp-podpod.com/stg`
- **production**: `https://sp-podpod.com`

### JWT
```yaml
jwt:
  algorithm: "HS256"
  access_token_expire_minutes: 30
```

### Chat Service
```yaml
chat:
  use_websocket: false  # true: WebSocket, false: Sendbird
```

### Server
```yaml
server:
  debug: true  # 개발 환경만 true
  host: "127.0.0.1"
  port: 8000
  reload: true
```

### Infisical
```yaml
infisical:
  enabled: true
  env: "dev"  # dev, stg, prod
```

## 설정 우선순위

1. 환경 변수 (최우선)
2. Config YAML 파일
3. 코드 기본값

## 파일 위치 자동 설정

### Uploads
- **local/development**: `services/api/uploads/dev/`
  - `pods/images/` - Pod 이미지
  - `pods/thumbnails/` - Pod 썸네일
  - `users/profiles/` - 사용자 프로필 이미지
  - `artists/` - 아티스트 이미지
  - 접근 URL: `http://localhost:8000/uploads/...`
- **staging**: `/Users/Shared/Projects/PodPod/uploads/stg/`
  - `pods/images/` - Pod 이미지
  - `pods/thumbnails/` - Pod 썸네일
  - `users/profiles/` - 사용자 프로필 이미지
  - `artists/` - 아티스트 이미지
  - 접근 URL: `https://sp-podpod.com/stg/uploads/...` (Nginx location: `/stg/uploads/`)
- **production**: `/Users/Shared/Projects/PodPod/uploads/prod/`
  - `pods/images/` - Pod 이미지
  - `pods/thumbnails/` - Pod 썸네일
  - `users/profiles/` - 사용자 프로필 이미지
  - `artists/` - 아티스트 이미지
  - 접근 URL: `https://sp-podpod.com/uploads/...` (Nginx location: `/uploads/`)

### Logs
- **local/development**: `services/api/logs/dev/`
- **staging**: `/Users/Shared/Projects/PodPod/logs/stg/`
- **production**: `/Users/Shared/Projects/PodPod/logs/prod/`
