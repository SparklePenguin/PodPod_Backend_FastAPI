# 환경 변수 가이드

## 환경별 설정 방식

### Local/Dev 환경
- **Config 파일**: `config.dev.yaml` (비민감 설정)
- **환경 변수**: `.env` 파일 + Infisical (민감 정보)

### Staging/Production 환경
- **Config 파일**: `config.stg.yaml` / `config.prod.yaml` (비민감 설정)
- **환경 변수**: Infisical 전체 사용 (모든 민감 정보)

## 필수 환경 변수 (Infisical)

### 데이터베이스
```bash
MYSQL_PASSWORD=your-password
```

### JWT
```bash
SECRET_KEY=your-secret-key
```

### OAuth (사용하는 것만)
```bash
KAKAO_CLIENT_ID=your-client-id
KAKAO_CLIENT_SECRET=your-secret

NAVER_CLIENT_ID=your-client-id
NAVER_CLIENT_SECRET=your-secret

GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret

APPLE_CLIENT_ID=your-client-id
APPLE_TEAM_ID=your-team-id
APPLE_KEY_ID=your-key-id
APPLE_PRIVATE_KEY=your-private-key
```

## 특이사항

### OAuth Redirect URI
- **환경 변수 불필요**: config 파일의 `base_url`(호스트+포트/경로 포함)을 참조해 자동 생성
- **생성 방식**: `{base_url}/auth/{provider}/callback`
- **예시**:
  - Dev: `http://localhost:8000` → `http://localhost:8000/auth/kakao/callback`
  - Staging: `https://sp-podpod.com/stg` → `https://sp-podpod.com/stg/auth/kakao/callback`
  - Prod: `https://sp-podpod.com` → `https://sp-podpod.com/auth/kakao/callback`
