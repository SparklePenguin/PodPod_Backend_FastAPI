# GCP 배포 가이드

이 문서는 PodPod Backend를 Google Cloud Platform (GCP)에 배포하는 방법을 설명합니다.

## 🚀 빠른 배포

### 1. 사전 준비

```bash
# Google Cloud CLI 설치 및 로그인
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 필요한 API 활성화
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. 환경 변수 설정

`deploy.sh` 파일에서 프로젝트 ID를 수정하세요:

```bash
PROJECT_ID="your-actual-project-id"
```

### 3. 배포 실행

```bash
# 배포 스크립트 실행
./deploy.sh
```

## 🔧 수동 배포

### 1. Docker 이미지 빌드

```bash
# 이미지 빌드
docker build -t gcr.io/YOUR_PROJECT_ID/podpod-backend .

# 이미지 푸시
docker push gcr.io/YOUR_PROJECT_ID/podpod-backend
```

### 2. Cloud Run 배포

```bash
gcloud run deploy podpod-backend \
  --image gcr.io/YOUR_PROJECT_ID/podpod-backend \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 100 \
  --timeout 300
```

## 🔐 시크릿 관리

### Secret Manager 설정

```bash
# 데이터베이스 설정
gcloud secrets create db-host --data-file=- <<< "your-db-host"
gcloud secrets create db-password --data-file=- <<< "your-db-password"

# JWT 설정
gcloud secrets create jwt-secret-key --data-file=- <<< "your-jwt-secret"

# OAuth 설정
gcloud secrets create google-client-id --data-file=- <<< "your-google-client-id"
gcloud secrets create kakao-client-id --data-file=- <<< "your-kakao-client-id"

# Firebase 설정
gcloud secrets create firebase-service-account-key --data-file=- <<< '{"type": "service_account", ...}'
```

### Cloud Run에서 시크릿 사용

```bash
gcloud run services update podpod-backend \
  --region asia-northeast3 \
  --set-secrets="DB_HOST=db-host:latest,DB_PASSWORD=db-password:latest,JWT_SECRET_KEY=jwt-secret-key:latest"
```

## 📊 모니터링

### 로그 확인

```bash
# Cloud Run 로그 확인
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=podpod-backend" --limit 50

# 실시간 로그 스트리밍
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=podpod-backend"
```

### 메트릭 확인

```bash
# 서비스 상태 확인
gcloud run services describe podpod-backend --region asia-northeast3

# 헬스체크
curl https://your-service-url/health
```

## 🔄 CI/CD 설정

### Cloud Build 트리거 설정

```bash
# GitHub 연결
gcloud builds triggers create github \
  --repo-name=your-repo \
  --repo-owner=your-username \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

## 🛠️ 트러블슈팅

### 일반적인 문제들

1. **메모리 부족 오류**
   ```bash
   # 메모리 증가
   gcloud run services update podpod-backend --memory 4Gi
   ```

2. **타임아웃 오류**
   ```bash
   # 타임아웃 증가
   gcloud run services update podpod-backend --timeout 600
   ```

3. **환경 변수 문제**
   ```bash
   # 환경 변수 확인
   gcloud run services describe podpod-backend --region asia-northeast3
   ```

### 로그 분석

```bash
# 에러 로그만 필터링
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=podpod-backend AND severity>=ERROR" --limit 20

# 특정 시간대 로그
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=podpod-backend" --freshness=1h
```

## 📝 환경 변수 목록

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `ENVIRONMENT` | 환경 (production/development) | ✅ |
| `DB_HOST` | 데이터베이스 호스트 | ✅ |
| `DB_PASSWORD` | 데이터베이스 비밀번호 | ✅ |
| `JWT_SECRET_KEY` | JWT 서명 키 | ✅ |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | ✅ |
| `KAKAO_CLIENT_ID` | Kakao OAuth 클라이언트 ID | ✅ |
| `FIREBASE_SERVICE_ACCOUNT_KEY` | Firebase 서비스 계정 키 | ✅ |

## 🔗 유용한 링크

- [Cloud Run 문서](https://cloud.google.com/run/docs)
- [Cloud Build 문서](https://cloud.google.com/build/docs)
- [Secret Manager 문서](https://cloud.google.com/secret-manager/docs)
- [Container Registry 문서](https://cloud.google.com/container-registry/docs)
