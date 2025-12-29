# Scraping Service

아티스트 이미지 스크래핑, 정제를 통한 DB 업데이트 서비스

## 주요 기능

- **아티스트 이미지 스크래핑**: 외부 소스에서 이미지 수집
- **데이터 정제**: 이미지 메타데이터 추출 및 검증
- **DB 동기화**: 아티스트/유닛 데이터 업데이트

## 실행

```bash
# 루트에서 실행
./scripts/start-local.sh  # 로컬 환경
./scripts/start-dev.sh    # Docker 환경
```

## 구조

```
app/
├── routers/         # API 라우터
├── services/        # 비즈니스 로직
├── repositories/    # DB 액세스
└── main.py          # FastAPI 앱
```

## API 문서

http://localhost:8001/docs
