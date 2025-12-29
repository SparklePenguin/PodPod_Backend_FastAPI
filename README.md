# PodPod Backend

K-POP 아티스트 기반 소셜 플랫폼 백엔드

## 빠른 시작

### 설치 (최초 1회)
```bash
./scripts/setup-dependencies.sh  # 시스템 의존성 설치
./scripts/install-packages.sh    # Python 패키지 설치
```

### 실행
```bash
./scripts/start-local.sh  # 로컬 환경
./scripts/start-dev.sh    # Docker 환경
```

## 프로젝트 구조

```
PodPod_Backend_FastAPI/
├── services/
│   ├── api/          # 메인 API 서비스 (8000)
│   └── scraping/     # 아티스트 스크래핑 서비스 (8001)
├── scripts/          # 실행 및 관리 스크립트
├── docs/             # 문서
└── infra/            # 인프라 설정
```

## 기술 스택

- **Framework**: FastAPI
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT, OAuth (Google, Apple, Kakao, Naver)
- **Package Manager**: uv
- **Environment**: Infisical

## 문서

- [스크립트 가이드](/docs/scripts-info.md)
- [환경 변수 가이드](/docs/env-info.md)
- [Config 파일 가이드](/docs/config-info.md)
- [개발 의존성 가이드](/docs/dev-dependencies-info.md)
- [서비스 구조](/services/README.md)
- API Docs: http://localhost:8000/docs
