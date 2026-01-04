# API Service

PodPod 메인 API 서비스

## 주요 기능

- **사용자**: 프로필, 알림 설정, 차단
- **인증**: JWT, OAuth (Google, Apple, Kakao, Naver)
- **Pod**: 생성, 모집, 지원, 리뷰, 좋아요
- **아티스트**: 조회, 팔로우, 스케줄, 제안
- **성향 테스트**: 설문, 결과, 매칭
- **알림**: 팔로우, Pod, 리뷰 관련 알림
- **신고**: 사용자, Pod, 리뷰 신고
- **채팅**: WebSocket 실시간 채팅
- **관리자**: 시스템 관리, FCM

## 실행

```bash
# 루트에서 실행
./scripts/start-local.sh  # 로컬 환경
./scripts/start-dev.sh    # Docker 환경
```

## 구조

```
app/
├── features/        # 기능별 모듈
│   ├── users/
│   ├── auth/
│   ├── pods/
│   ├── artists/
│   └── ...
├── core/            # 핵심 설정 ㅇ
├── common/          # 공통 모듈
└── deps/            # 의존성
```

## API 문서

http://localhost:8000/docs
