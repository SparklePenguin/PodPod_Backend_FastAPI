# PodPod Backend

K-POP 아티스트 기반 소셜 플랫폼 백엔드

## 문서

- [스크립트 가이드](/docs/scripts-info.md)
- [환경 변수 가이드](/docs/env-info.md)
- [Config 파일 가이드](/docs/config-info.md)
- [개발 의존성 가이드](/docs/dev-dependencies-info.md)
- [서비스 구조](/services/README.md)
- API Docs: http://localhost:8000/docs

## 기술 스택

- **Framework**: FastAPI
- **Database**: MySQL
- **Cache/Session**: Redis
- **ORM**: SQLAlchemy
- **Authentication**: JWT, OAuth (Google, Apple, Kakao, Naver)
- **Package Manager**: uv
- **Environment**: Infisical

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

# 실행 가이드

## 터널링

PodPod은 DataBase, Redis 등 기타 인프라가 서버 호스트에 존재합니다. 따라서 로컬에서 작업 시 터널링을 통해 접근할 수 있습니다.

- DataBase
    ```sh
    $ ssh  -i [SSH-KEY] -N -L 3306:127.0.0.1:3306 [USER_NAME]@[SERVER-IP]
    ```

- Redis
    ```sh
    $ ssh  -i [SSH-KEY] -N -L 6379:127.0.0.1:6379 [USER_NAME]@[SERVER-IP]
    ```

## 실행

- 프로젝트의 주요 환경변수는 `infisical`과 `yam`" 파일을 통해 주입받음. 따라서 프로젝트 실행 시 하기 명령을 통한 실행 권장
  ```sh
  $ infisical run --env=dev --path=/backend -- docker-compose -f ./deploy/docker-compose.dev.yml up --build
  ```
  - `env` : dev, stg, prd
