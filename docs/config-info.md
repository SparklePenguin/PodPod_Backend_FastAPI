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
- **local/dev**: `services/api/uploads/{local|dev}/`
- **staging**: `/srv/uploads/podpod/stg/`
- **production**: `/srv/uploads/podpod/prod/`

### Logs
- **local/dev**: `services/api/logs/{local|dev}/`
- **staging**: `/srv/logs/podpod/stg/`
- **production**: `/srv/logs/podpod/prod/`
