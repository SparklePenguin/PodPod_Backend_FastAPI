# PodPod Services

마이크로서비스 아키텍처 기반 백엔드 서비스

## 서비스 구성

### API Service (`./api`)
- 메인 FastAPI 애플리케이션
- 사용자, Pod, 팔로우, 알림 등 핵심 기능 제공
- Port: 8000

### Scraping Service (`./scraping`)
- 아티스트 이미지 스크래핑, 정제를 통한 DB 업데이트
- Port: 8001

## 실행

스크립트를 통한 실행 권장:

```bash
./scripts/start-local.sh  # 로컬 환경 (가상환경)
./scripts/start-dev.sh    # Docker 개발 환경
```

자세한 내용은 `/docs/scripts-info.md` 참조
