# TODO 리스트

## 데이터 중복 문제

### 1. 같은 아티스트의 이름 중복 저장
- `/api/v1/artists/mvp` API에서 같은 아티스트의 같은 이름이 여러 번 저장됨
- 예: 한유진(artist_id=1526)의 "한유진" 이름이 2개 저장
- 영향: `find_artist_by_member_ko_name`에서 `MultipleResultsFound` 에러 발생

### 2. 다른 그룹 간 아티스트 이름 중복
- 서로 다른 그룹에 같은 이름의 멤버가 존재
- 예: "마크"가 8개 그룹에, "김채원"이 6개 그룹에 존재
- 영향: 멤버 매칭 시 잘못된 아티스트로 연결될 수 있음

### 해결 필요
- [ ] `/api/v1/artists/mvp` API 중복 생성 방지 로직 추가
- [ ] 기존 중복 데이터 정리
- [ ] 멤버 매칭 로직 개선 (그룹 컨텍스트 고려)

### 임시 해결책
- `find_artist_by_member_ko_name`에 `.limit(1)` 추가 (완료)

## DTO 정리

### Page Request 상속 구조 개선
- [ ] 공통 `PageRequest` 클래스 생성 (page, page_size 필드)
- [ ] `PodSearchRequest`가 `PageRequest` 상속하도록 수정
- [ ] 다른 검색 DTO들도 동일한 구조로 통일
- [ ] 페이지네이션 관련 중복 코드 제거
