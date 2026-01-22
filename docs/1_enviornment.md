# 환경변수 관리 가이드

## 1. 문서 목적

본 문서는 프로젝트 전반에서 사용되는 **환경변수 관리 체계와 사용 기준**을 명확히 설명하는 것을 목적으로 합니다.

환경변수는 보안 민감도, 변경 주기, 사용 맥락에 따라 서로 다른 방식으로 관리되며, 본 문서는 각 방식의 **역할 분리 원칙**, **사용 위치**, **주의 사항**을 기술합니다.

이 문서는 다음 대상을 독자로 가정합니다.

* 신규 프로젝트 참여자
* 로컬 개발 및 배포 작업을 수행하는 개발자
* 운영 및 보안 설정을 검토하는 담당자

---

## 2. 환경변수 관리 체계 개요

본 프로젝트에서는 환경변수를 다음 세 가지 방식으로 관리합니다.

* YAML 설정 파일 (`*.yaml`)
* Infisical (Secret Manager)
* `.env` 파일

각 방식은 **대체 관계가 아닌 보완 관계**이며, 아래 기준에 따라 명확히 구분하여 사용해야 합니다.

| 구분        | 주 사용 목적    | 저장 위치             | 보안 민감도 |
|-----------|------------|-------------------|--------|
| YAML      | 비민감 설정 값   | 저장소 포함            | 낮음     |
| Infisical | 비밀 정보      | 외부 Secret Manager | 높음     |
| .env      | 배포/자동화용 변수 | 로컬 파일             | 중간     |

---

## 3. YAML 환경변수

### 3.1 사용 목적

YAML 환경변수는 다음과 같은 특성을 가진 설정 값을 관리하는 데 사용됩니다.

* 외부 노출 시 보안 리스크가 낮은 값
* 환경별로 값은 달라질 수 있으나 구조는 동일한 설정
* 애플리케이션 동작에 필요한 기본 구성 정보

### 3.2 파일 위치 및 구성

* YAML 파일은 `deploy/config` 디렉터리 하위에 위치합니다.
* 배포 환경별로 파일이 분리되어 있습니다.

    * 예: `config.local.yaml`, `config.dev.yaml`, `config.prod.yaml`

### 3.3 애플리케이션 전달 방식

YAML 설정 파일은 Docker Compose를 통해 컨테이너 내부로 전달됩니다.

* `environment`

    * 애플리케이션이 참조할 설정 파일 경로를 환경변수로 전달
* `volumes`

    * 실제 YAML 파일을 컨테이너 내부 경로에 마운트

```yaml
environment:
  CONFIG_FILE: [ YAML_PATH ]
  ...
volumes:
  - ./config/config.local.yaml:/app/config/config.local.yaml
```

> **주의**
> API Key, Token, Password 등 민감 정보는 YAML 파일에 절대 포함해서는 안 됩니다.

---

## 4. Infisical

### 4.1 사용 목적

Infisical은 다음과 같은 **고보안 환경변수**를 관리하기 위해 사용됩니다.

* 외부에 노출될 경우 심각한 보안 문제가 발생하는 값
* 저장소에 커밋되어서는 안 되는 Secret 정보
* 런타임 시점에만 주입되어야 하는 설정 값

### 4.2 동작 방식

* Infisical은 애플리케이션 실행 시점에 환경변수를 **Runtime Injection** 방식으로 주입합니다.
* 컨테이너 이미지 및 저장소에는 실제 값이 남지 않습니다.

### 4.3 실행 방법

Infisical을 사용하여 Docker Compose를 실행할 경우 다음 명령어를 사용합니다.

```shell
infisical run \
		--projectId=$(INFISICAL_PROJECT_ID) \
		--env=dev \
		--path=/backend \
		-- docker-compose -f ./deploy/docker-compose.dev.yml up --build -d
```

---

## 5. .env 파일

### 5.1 사용 목적

`.env` 파일은 애플리케이션 설정을 위한 용도가 아니라, **개발 및 배포 자동화**를 위한 보조 환경변수를 관리하는 데 사용됩니다.

* Makefile 실행 시 참조
* 로컬 개발 환경 및 서버 배포 작업 지원

### 5.2 관리 원칙

* `.env` 파일은 저장소에 커밋하지 않습니다.
* 개인 또는 환경별로 값이 달라질 수 있습니다.

### 5.3 필수 환경변수

```shell
SSH_USER=
SSH_KEY_PATH=
SERVER_IP=

INFISICAL_PROJECT_ID=
INFISICAL_TOKEN= 
```

각 항목의 의미는 다음과 같습니다.

* **SSH_USER**
    - 배포 대상 서버에 접속할 사용자 계정
* **SSH_KEY_PATH**
    - SSH 인증에 사용되는 개인 키 파일의 로컬 경로
* **SERVER_IP**
    - 배포 대상 서버의 IP 주소
* **INFISICAL_PROJECT_ID**
    - INFISICAL의 환경변수가 설정된 프로젝트 ID
* **INFISICAL_TOKEN**
    - INFISICAL의 서비스 토큰

---

## 6. 운영 가이드 요약

* 설정 값의 보안 민감도를 기준으로 관리 방식을 선택합니다.
* Secret 정보는 반드시 Infisical을 통해서만 관리합니다.
* YAML 파일은 구조 중심의 설정만 포함하도록 유지합니다.
* `.env`는 배포 자동화 전용으로 사용하며 애플리케이션 설정에 사용하지 않습니다.

본 원칙을 준수함으로써 환경변수 관리의 **일관성**, **보안성**, **유지보수성**을 확보할 수 있습니다.
