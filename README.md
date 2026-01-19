# PodPod Backend

K-POP 아티스트 기반 소셜 플랫폼 백엔드

## 문서

- [환경 변수 가이드](/docs/1_enviornment.md)

## API Docs

- Local : http://localhost:8000/docs
- DEV : https://dev.sp-podpod.com/docs
- STG : https://stg.sp-podpod.com/docs
- PRD : https://sp-podpod.com/docs

## 프로젝트 스택

- **Framework**: FastAPI
- **Database**: MySQL
- **Cache/Session**: Redis
- **ORM**: SQLAlchemy
- **Authentication**: JWT, OAuth (Google, Apple, Kakao, Naver)
- **Package Manager**: uv
- **Environment**: Infisical

## 프로젝트 구조

- STRUCTURE
  ```text
  ╰─$ tree -L 2 -I venv -I *.log -I scripts -I __pycache__
  .
  ├── commit-prompt.txt # 일관된 커밋 컨벤션 작성을 위한 prompt 파일
  ├── deploy
  │   ├── config
  │   ├── docker-compose.dev.yml
  │   ├── docker-compose.prod.yml
  │   ├── docker-compose.stg.yml
  │   ├── prometheus
  │   ├── services
  │   └── shared
  ├── docker
  │   └── docker-compose.local.yml # 로컬에서 환경 구성 시 사용
  ├── docs # 문서
  │   ├── *.md
  ├── makefile # 배포 관련 명령
  ├── README.md
  ├── services
  │   ├── api # 메인 API 서비스 (8000)
  │   ├── README.md
  │   └── scraping # 아티스트 스크래핑 서비스 (8001)
  ├── shared
  │   ├── __init__.py
  │   ├── models
  │   ├── schemas
  │   └── utils
  └── uploads
      ├── dev
      └── pods
  ```

## 빠른 시작

### 설치

- 가상환경 생성 및 활성화
  ```shell
  $ python3 -m venv venv
  $ source ./venv/bin/activate
  ```
- PIP를 활용한 패키지 설치
  ```shell
  $ pip install -r services/api/requirements.txt
  ```

# 실행 가이드

## 터널링

PodPod은 DataBase, Redis 등 기타 인프라가 서버 호스트에 존재합니다. 따라서 로컬에서 작업 시 터널링을 통해 접근할 수 있습니다.

- Base Command
    ```sh
    # DB
    $ ssh  -i [SSH-KEY] -N -L 3306:127.0.0.1:3306 [USER_NAME]@[SERVER-IP] 
    # REDIS
    $ ssh  -i [SSH-KEY] -N -L 6379:127.0.0.1:6379 [USER_NAME]@[SERVER-IP] 
    # VNC
    $ ssh  -i [SSH-KEY] -N -L 5900:127.0.0.1:5900 [USER_NAME]@[SERVER-IP] 
    ```

상위에 기술된 Base Command를 makefile을 통해서도 실행 가능합니다.

- Makefile
  ``` shell
  $ make infra.connect
  ```

## 실행

- 프로젝트의 실행은 `docker-comopse.*.yml` 을 통해 실행됩니다.
  ```sh
  $ infisical run --env=dev --path=/backend -- docker-compose -f ./deploy/docker-compose.dev.yml up --build
  ```
    - `env` : dev, stg, prd
- 상위에 기술된 Command를 makefile을 통해서도 실행가능합니다.
  ```shell
  $ make deploy.local
  ```
