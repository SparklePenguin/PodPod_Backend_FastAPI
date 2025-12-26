# 스크래핑 서비스 아키텍처 가이드

## 상황 분석

**요구사항:**
- 주기적으로 아티스트 이미지 스크래핑
- 스크래핑한 이미지 업로드
- 안정적이고 확장 가능한 구조

**스크래핑 작업의 특성:**
- ⚠️ CPU/네트워크 집약적 (메인 API 성능에 영향)
- ⚠️ 실패 가능성 높음 (외부 사이트 변경, 네트워크 이슈)
- ✅ 독립적 실행 (메인 API와 의존성 낮음)
- ✅ 다른 스케일링 요구사항 (메인 API와 다름)
- ✅ 다른 배포 주기 (스크래핑 로직 변경 시 메인 API 재배포 불필요)

---

## 아키텍처 옵션 비교

### Option 1: 백그라운드 태스크 (모놀리식)

```
┌─────────────────────────────────────────────┐
│         단일 FastAPI 애플리케이션            │
│                                             │
│  ┌──────────────┐    ┌──────────────────┐  │
│  │   API        │    │  Background      │  │
│  │   Endpoints  │    │  Task Worker     │  │
│  │              │    │  (Celery/        │  │
│  │              │    │   APScheduler)   │  │
│  └──────────────┘    └──────────────────┘  │
│         │                     │             │
│         └─────────┬───────────┘             │
│                   │                         │
│            ┌──────▼──────┐                  │
│            │  Database   │                  │
│            └─────────────┘                  │
└─────────────────────────────────────────────┘
```

**장점:**
- ✅ 간단한 구조 (하나의 코드베이스)
- ✅ 코드 공유 용이 (models, services)
- ✅ 낮은 운영 복잡도
- ✅ 빠른 개발 (초기 구축 빠름)
- ✅ 로컬 개발 편리

**단점:**
- ❌ 리소스 격리 불가 (스크래핑이 API 성능 저하)
- ❌ 독립적 스케일링 불가
- ❌ 스크래핑 실패 시 전체 서비스 영향 가능
- ❌ 배포 시 전체 재시작 필요

**추천 상황:**
- 프로젝트 초기 (MVP)
- 스크래핑 빈도 낮음 (하루 1-2회)
- 데이터 양 적음 (수십~수백 건)
- 팀 규모 작음 (1-3명)

---

### Option 2: 마이크로서비스 분리 ⭐ 추천

```
┌─────────────────────┐      ┌──────────────────────┐
│   Main API Service  │      │  Scraping Service    │
│   (FastAPI)         │      │  (별도 Container)    │
│                     │      │                      │
│  - User API         │      │  - Scheduler         │
│  - Pod API          │      │  - Scraper Worker    │
│  - Artist API       │      │  - Image Uploader    │
│                     │      │                      │
└──────────┬──────────┘      └──────────┬───────────┘
           │                            │
           │         ┌──────────────────┤
           │         │                  │
    ┌──────▼─────────▼──────┐    ┌─────▼──────┐
    │   Shared Database     │    │   Redis    │
    │   (Artists, Images)   │    │   Queue    │
    └───────────────────────┘    └────────────┘
```

**장점:**
- ✅ **리소스 격리** (스크래핑이 메인 API에 영향 없음)
- ✅ **독립적 스케일링** (스크래핑만 인스턴스 증가)
- ✅ **장애 격리** (스크래핑 실패해도 메인 API 정상)
- ✅ **독립적 배포** (스크래핑 로직 변경 시 메인 API 무중단)
- ✅ **기술 스택 자유도** (스크래핑에 최적화된 라이브러리 사용)
- ✅ **모니터링 분리** (리소스 사용량 개별 추적)

**단점:**
- ❌ 높은 운영 복잡도 (여러 컨테이너 관리)
- ❌ 인프라 비용 증가 (최소 2개 컨테이너)
- ❌ 네트워크 통신 오버헤드
- ❌ 코드 중복 가능성 (shared 모듈 필요)

**추천 상황:**
- 프로덕션 환경 (안정성 중요)
- 스크래핑 빈도 높음 (시간당 1회 이상)
- 데이터 양 많음 (수천~수만 건)
- 확장 계획 있음

---

## 추천 아키텍처: 하이브리드 접근

### 단계별 마이그레이션 전략

#### Phase 1: 모놀리식 시작 (MVP)
```python
# 메인 FastAPI 앱에 APScheduler 추가
# 빠른 검증, 낮은 복잡도
```

#### Phase 2: 작업 분리 (성장기)
```python
# Celery Worker 분리 (같은 코드베이스, 다른 프로세스)
# 리소스 격리 시작
```

#### Phase 3: 마이크로서비스 분리 (성숙기)
```python
# 완전히 독립적인 서비스
# 독립 배포, 독립 스케일링
```

---

## 추천: Option 2 (마이크로서비스 분리)

스크래핑 작업의 특성상 **분리를 추천**합니다.

### 이유

1. **성능 격리**
   - 스크래핑은 CPU/네트워크 집약적
   - 메인 API 응답 속도에 영향 없음

2. **안정성**
   - 외부 사이트 변경으로 스크래핑 실패해도 메인 API는 정상 작동
   - 독립적인 재시작 가능

3. **확장성**
   - 아티스트 수 증가 시 스크래핑 서비스만 스케일 아웃
   - 비용 효율적

4. **배포 유연성**
   - 스크래핑 로직 변경 시 메인 API 무중단
   - 실험적 기능 테스트 용이

---

## 구현 가이드 (마이크로서비스)

### 디렉토리 구조

```
project-root/
├── services/
│   ├── api/                    # 메인 FastAPI 서비스
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── scraping/               # 스크래핑 서비스 ⭐
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py         # Scheduler 진입점
│       │   ├── scrapers/       # 스크래퍼 모듈
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   └── artist_image_scraper.py
│       │   ├── uploaders/      # 업로더 모듈
│       │   │   └── gcs_uploader.py
│       │   └── config.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── pyproject.toml
│
├── shared/                      # 공유 모듈
│   ├── models/                  # SQLAlchemy 모델
│   └── utils/
│
└── docker-compose.yml
```

### 1. Scraping Service 구현

#### `services/scraping/app/main.py`

```python
"""
Scraping Service - 주기적 아티스트 이미지 스크래핑
"""
import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.scrapers.artist_image_scraper import ArtistImageScraper
from app.database import init_db, get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def scrape_artist_images():
    """아티스트 이미지 스크래핑 작업"""
    logger.info("=== Artist Image Scraping Started ===")
    start_time = datetime.now()

    try:
        async with get_db() as db:
            scraper = ArtistImageScraper(db)
            result = await scraper.scrape_all_artists()

            logger.info(
                f"✅ Scraping completed: "
                f"success={result['success']}, "
                f"failed={result['failed']}, "
                f"duration={(datetime.now() - start_time).total_seconds()}s"
            )

    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}", exc_info=True)
    finally:
        logger.info("=== Artist Image Scraping Finished ===")


async def main():
    """메인 스케줄러"""
    logger.info("🚀 Scraping Service Starting...")

    # 데이터베이스 초기화
    await init_db()

    # 스케줄러 생성
    scheduler = AsyncIOScheduler()

    # 스케줄 등록
    # 매일 오전 3시 실행
    scheduler.add_job(
        scrape_artist_images,
        trigger=CronTrigger(hour=3, minute=0),
        id="scrape_artist_images",
        name="Scrape artist images",
        replace_existing=True,
    )

    # 테스트용: 10분마다 실행
    if settings.ENVIRONMENT == "development":
        scheduler.add_job(
            scrape_artist_images,
            trigger=CronTrigger(minute="*/10"),
            id="scrape_artist_images_dev",
            name="Scrape artist images (dev)",
            replace_existing=True,
        )

    scheduler.start()
    logger.info("✅ Scheduler started")

    # 즉시 한 번 실행 (선택)
    if settings.RUN_ON_STARTUP:
        await scrape_artist_images()

    # 서비스 계속 실행
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("⏹️  Shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

#### `services/scraping/app/scrapers/artist_image_scraper.py`

```python
"""
아티스트 이미지 스크래퍼
"""
import logging
from typing import Dict

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from app.uploaders.gcs_uploader import GCSUploader
from shared.models.artist import Artist, ArtistImage

logger = logging.getLogger(__name__)


class ArtistImageScraper:
    """아티스트 이미지 스크래핑"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.uploader = GCSUploader()
        self.client = httpx.AsyncClient(timeout=30.0)

    async def scrape_all_artists(self) -> Dict[str, int]:
        """모든 아티스트의 이미지 스크래핑"""
        # 이미지가 없는 아티스트 조회
        artists = await self.db.execute(
            """
            SELECT a.* FROM artists a
            LEFT JOIN artist_images ai ON a.id = ai.artist_id
            WHERE ai.id IS NULL OR a.updated_at < NOW() - INTERVAL '30 days'
            LIMIT 100
            """
        )
        artists = artists.scalars().all()

        success_count = 0
        failed_count = 0

        for artist in artists:
            try:
                image_url = await self.scrape_artist_image(artist)
                if image_url:
                    # 이미지 DB 저장
                    artist_image = ArtistImage(
                        artist_id=artist.id,
                        image_url=image_url,
                        source="scraping",
                    )
                    self.db.add(artist_image)
                    await self.db.commit()
                    success_count += 1
                    logger.info(f"✅ {artist.name}: {image_url}")
                else:
                    failed_count += 1
                    logger.warning(f"⚠️ {artist.name}: No image found")

            except Exception as e:
                failed_count += 1
                logger.error(f"❌ {artist.name}: {e}")

        return {"success": success_count, "failed": failed_count}

    async def scrape_artist_image(self, artist: Artist) -> str | None:
        """단일 아티스트 이미지 스크래핑"""
        # 검색 URL 생성 (예: Google Images)
        search_url = f"https://example.com/search?q={artist.name}"

        response = await self.client.get(search_url)
        soup = BeautifulSoup(response.text, "html.parser")

        # 이미지 URL 추출 (사이트마다 다름)
        img_tag = soup.find("img", class_="artist-image")
        if not img_tag:
            return None

        image_url = img_tag.get("src")

        # 이미지 다운로드 및 GCS 업로드
        image_data = await self.client.get(image_url)
        gcs_url = await self.uploader.upload(
            image_data.content, f"artists/{artist.id}.jpg"
        )

        return gcs_url

    async def __del__(self):
        await self.client.aclose()
```

### 2. Docker 구성

#### `services/scraping/Dockerfile`

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY ../shared/ ./shared/

# 실행
CMD ["python", "-m", "app.main"]
```

#### `services/scraping/requirements.txt`

```txt
# Scheduler
apscheduler==3.10.4

# Scraping
httpx==0.27.0
beautifulsoup4==4.12.3
lxml==5.1.0

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0

# Cloud Storage
google-cloud-storage==2.14.0

# Monitoring
prometheus-client==0.19.0
```

### 3. Docker Compose

#### `docker-compose.yml`

```yaml
version: '3.8'

services:
  # 메인 API 서비스
  api:
    build:
      context: ./services/api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ENVIRONMENT=production
    depends_on:
      - postgres
    restart: unless-stopped

  # 스크래핑 서비스 ⭐
  scraping:
    build:
      context: .
      dockerfile: ./services/scraping/Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GCS_BUCKET_NAME=${GCS_BUCKET_NAME}
      - GCS_CREDENTIALS=${GCS_CREDENTIALS}
      - ENVIRONMENT=production
      - RUN_ON_STARTUP=false
    depends_on:
      - postgres
    restart: unless-stopped
    # 리소스 제한
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # 데이터베이스
  postgres:
    image: postgres:16
    environment:
      - POSTGRES_DB=podpod
      - POSTGRES_USER=podpod
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### 4. 배포 (GCP Cloud Run 예시)

```bash
# API 서비스 배포
gcloud run deploy podpod-api \
  --source ./services/api \
  --region asia-northeast3 \
  --allow-unauthenticated

# 스크래핑 서비스 배포 (Cloud Run Jobs)
gcloud run jobs create podpod-scraping \
  --source ./services/scraping \
  --region asia-northeast3 \
  --schedule="0 3 * * *"  # 매일 오전 3시
```

---

## 비용 분석

### Option 1 (모놀리식)
- Cloud Run 인스턴스: 1개
- 월 비용: ~$20-50

### Option 2 (마이크로서비스)
- Cloud Run API: 1개 (항상 실행)
- Cloud Run Jobs (스크래핑): 1일 1회, 30분 실행
- 월 비용: ~$30-70 (+$10-20)

**결론**: 비용 차이 작음, 안정성/확장성 이득이 훨씬 큼

---

## 모니터링

### 메트릭 수집

```python
# services/scraping/app/metrics.py
from prometheus_client import Counter, Histogram, Gauge

scraping_total = Counter(
    "scraping_total", "Total scraping jobs", ["status"]
)

scraping_duration = Histogram(
    "scraping_duration_seconds", "Scraping duration"
)

artists_scraped = Gauge(
    "artists_scraped_total", "Total artists scraped"
)
```

### 로그 모니터링

```python
# 구조화된 로그
logger.info(
    "Scraping completed",
    extra={
        "success_count": 150,
        "failed_count": 5,
        "duration_seconds": 120.5,
    }
)
```

---

## 최종 추천

### ✅ 마이크로서비스 분리 (Option 2)

**이유:**
1. 스크래핑은 독립적 작업
2. 리소스 집약적 (메인 API 보호 필요)
3. 실패 시 격리 필요
4. 장기적으로 확장 가능

**구현 순서:**
1. `services/scraping` 디렉토리 생성
2. 스크래퍼 로직 구현
3. Dockerfile 작성
4. docker-compose.yml 업데이트
5. 로컬 테스트
6. Cloud Run Jobs로 배포

**예상 일정:**
- 설계: 0.5일
- 구현: 1-2일
- 테스트: 0.5일
- 배포: 0.5일
- **총 2-3일**

더 자세한 구현이 필요하면 말씀해주세요!
