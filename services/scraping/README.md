# PodPod Scraping Service

아티스트 이미지 생성 및 MVP 동기화를 담당하는 독립 서비스입니다.

## 기능

1. **아티스트 이미지 생성** (`POST /api/v1/artists/images/{artist_id}`)
   - 이미지 파일 업로드
   - 이미지 메타데이터 저장

2. **MVP 동기화** (`POST /api/v1/artists/mvp`)
   - BLIP 데이터와 MVP 목록 병합
   - 아티스트/유닛 데이터 동기화

## 실행 방법

### 로컬 실행

```bash
cd services/scraping

# 환경 변수 설정
cp .env.example .env
# .env 파일 수정

# 의존성 설치
pip install -r requirements.txt

# 실행
uvicorn app.main:app --reload --port 8001
```

### Docker 실행

```bash
# 빌드
docker build -t podpod-scraping -f services/scraping/Dockerfile .

# 실행
docker run -p 8001:8001 \
  -e DATABASE_URL=mysql+aiomysql://user:password@host:3306/podpod \
  podpod-scraping
```

## API 문서

실행 후 http://localhost:8001/docs에서 확인

## 디렉토리 구조

```
services/scraping/
├── app/
│   ├── routers/          # API 라우터
│   ├── services/         # 비즈니스 로직
│   ├── repositories/     # 데이터베이스 액세스
│   └── main.py          # FastAPI 앱
├── Dockerfile
├── requirements.txt
└── README.md
```

## 환경 변수

- `DATABASE_URL`: MySQL 데이터베이스 URL
- `ENVIRONMENT`: 환경 (development/production)
