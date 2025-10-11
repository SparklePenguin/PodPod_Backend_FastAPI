# PodPod Backend 개발 가이드

## 1. 데이터베이스
- 마이그레이션: `./migrate.sh` | SQL 실행: `./execute_sql.sh "쿼리"` | mysql 직접 사용 금지

## 2. 환경변수 (Infisical)
- Backend: `infisical secrets get KEY --env=dev --path=/Backend` | GoogleSheet: `--path=/GoogleSheet` | `run.py`가 자동 로드

## 3. 스키마 규칙
- 필드명: camelCase (Field(alias="camelCase")) | 타입/Enum 값: UpperCamelCase (POD_JOIN_REQUEST → PodJoinRequest) | model_config = {"populate_by_name": True} | typing import 확인

## 4. 응답 형식 (필수)
- BaseResponse: 모든 API는 `BaseResponse.ok(data, message_ko, http_status)` 사용 | PageDto: 리스트 조회 시 사용 (items, currentPage, pageSize, totalCount, totalPages, hasNext, hasPrev)

## 5. 서버
- 자동 재시작 (수동 재시작 불필요)