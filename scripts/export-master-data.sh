#!/bin/bash

# 마스터 데이터 추출 스크립트
# 운영 DB에서 초기 데이터를 추출하여 seeds/ 디렉토리에 저장

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📤 마스터 데이터 추출 시작..."
echo ""

# 추출할 테이블 목록
TABLES=(
    "artists"
    "artist_units"
    "artist_images"
    "artist_names"
    "artist_schedules"
    "schedule_members"
    "schedule_contents"
    "locations"
    "tendency_surveys"
    "tendency_results"
)

echo "📋 추출 대상 테이블:"
for table in "${TABLES[@]}"; do
    echo "  - $table"
done
echo ""

# 데이터베이스 정보 입력
read -p "Database host (기본: localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Database port (기본: 3306): " DB_PORT
DB_PORT=${DB_PORT:-3306}

read -p "Database name (기본: podpod): " DB_NAME
DB_NAME=${DB_NAME:-podpod}

read -p "Database user (기본: root): " DB_USER
DB_USER=${DB_USER:-root}

read -sp "Database password: " DB_PASSWORD
echo ""
echo ""

# 출력 파일 경로
OUTPUT_DIR="seeds"
OUTPUT_FILE="${OUTPUT_DIR}/master_data.sql"

# seeds 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

echo "🔄 데이터 추출 중..."

# mysqldump 실행
mysqldump \
    -h "$DB_HOST" \
    -P "$DB_PORT" \
    -u "$DB_USER" \
    -p"$DB_PASSWORD" \
    "$DB_NAME" \
    "${TABLES[@]}" \
    --no-create-info \
    --skip-triggers \
    --skip-add-locks \
    --skip-comments \
    --complete-insert \
    --compact > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    # 파일 크기 확인
    FILE_SIZE=$(wc -c < "$OUTPUT_FILE" | tr -d ' ')
    FILE_SIZE_KB=$((FILE_SIZE / 1024))

    echo ""
    echo -e "${GREEN}✅ 마스터 데이터 추출 완료!${NC}"
    echo ""
    echo "📁 파일 정보:"
    echo "  - 경로: $OUTPUT_FILE"
    echo "  - 크기: ${FILE_SIZE_KB}KB"
    echo ""

    # 각 테이블별 INSERT 문 개수 확인
    echo "📊 테이블별 레코드 수:"
    for table in "${TABLES[@]}"; do
        count=$(grep -c "INSERT INTO \`$table\`" "$OUTPUT_FILE" || echo "0")
        if [ "$count" -gt 0 ]; then
            echo "  - $table: ${count}개 INSERT 문"
        fi
    done
    echo ""

    echo "💡 다음 단계:"
    echo "  1. 개발 환경: ./scripts/start-dev.sh 실행 후"
    echo "     docker exec -i podpod-app-dev mysql -h db -u root -p podpod_dev < $OUTPUT_FILE"
    echo ""
    echo "  2. 스테이징 환경: 서버에서"
    echo "     mysql -u root -p podpod_staging < $OUTPUT_FILE"
    echo ""
else
    echo ""
    echo -e "${RED}❌ 데이터 추출 실패${NC}"
    exit 1
fi
