#!/bin/bash

# 로컬 환경 마스터 데이터 import 스크립트
# database/seeds/master_data.sql 파일을 로컬 MySQL DB에 적용

set -e

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.." || exit 1
PROJECT_ROOT=$(pwd)

echo "📥 로컬 환경 마스터 데이터 import"
echo ""

# 마스터 데이터 파일 확인
MASTER_DATA_FILE="database/seeds/master_data.sql"

if [ ! -f "$MASTER_DATA_FILE" ]; then
    echo "❌ 마스터 데이터 파일을 찾을 수 없습니다: $MASTER_DATA_FILE"
    echo ""
    echo "먼저 ./scripts/export-master-data.sh 를 실행하여 데이터를 추출하세요."
    exit 1
fi

# 파일 크기 확인
FILE_SIZE=$(wc -c < "$MASTER_DATA_FILE" | tr -d ' ')
FILE_SIZE_KB=$((FILE_SIZE / 1024))

echo "📁 파일 정보:"
echo "  - 경로: $MASTER_DATA_FILE"
echo "  - 크기: ${FILE_SIZE_KB}KB"
echo ""

# .env 파일에서 환경 변수 로드
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo "📝 .env.example을 복사하여 .env 파일을 생성하세요:"
    echo "  cp .env.example .env"
    exit 1
fi

echo "🔑 환경 변수 로드 (.env)"
export $(grep -v '^#' .env | xargs)

# 기본값 설정
MYSQL_HOST=${MYSQL_HOST:-localhost}
MYSQL_PORT=${MYSQL_PORT:-3306}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_DATABASE=${MYSQL_DATABASE:-podpod_local}

if [ -z "$MYSQL_PASSWORD" ]; then
    echo "❌ MYSQL_PASSWORD가 설정되지 않았습니다."
    echo "📝 .env 파일에 MYSQL_PASSWORD를 설정하세요."
    exit 1
fi

echo "🗄️  데이터베이스 정보:"
echo "  - Host: $MYSQL_HOST:$MYSQL_PORT"
echo "  - Database: $MYSQL_DATABASE"
echo "  - User: $MYSQL_USER"
echo ""

# 데이터베이스 연결 확인
if ! mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "USE $MYSQL_DATABASE" 2>/dev/null; then
    echo "❌ 데이터베이스 연결 실패"
    echo "📝 MySQL이 실행 중인지, 데이터베이스가 존재하는지 확인하세요."
    exit 1
fi

echo "✅ 데이터베이스 연결 확인"
echo ""

# 확인 메시지
echo "⚠️  경고: 기존 마스터 데이터가 모두 삭제됩니다!"
echo ""
read -p "계속하시겠습니까? (y/n): " -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 취소되었습니다."
    exit 0
fi

# 기존 마스터 데이터 삭제
echo "🗑️  기존 마스터 데이터 삭제 중..."

mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" <<EOF 2>&1 | grep -v "Warning" || true
SET FOREIGN_KEY_CHECKS=0;
TRUNCATE TABLE schedule_contents;
TRUNCATE TABLE schedule_members;
TRUNCATE TABLE artist_schedules;
TRUNCATE TABLE artist_images;
TRUNCATE TABLE artist_names;
TRUNCATE TABLE artist_units;
TRUNCATE TABLE artists;
TRUNCATE TABLE locations;
TRUNCATE TABLE tendency_results;
TRUNCATE TABLE tendency_surveys;
SET FOREIGN_KEY_CHECKS=1;
EOF

echo "✅ 기존 데이터 삭제 완료"
echo ""

# 마스터 데이터 import
echo "🔄 마스터 데이터 import 중..."

if mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < "$MASTER_DATA_FILE" 2>&1 | grep -v "Warning"; then
    echo ""
    echo "✅ 마스터 데이터 import 완료!"
    echo ""

    # 결과 확인
    echo "📊 Import 결과:"
    mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
        SELECT 'Artists' as 'Table', COUNT(*) as 'Count' FROM artists
        UNION ALL
        SELECT 'Artist Units', COUNT(*) FROM artist_units
        UNION ALL
        SELECT 'Artist Schedules', COUNT(*) FROM artist_schedules
        UNION ALL
        SELECT 'Locations', COUNT(*) FROM locations
        UNION ALL
        SELECT 'Tendencies', COUNT(*) FROM tendency_surveys;
    " 2>&1 | grep -v "Warning"
else
    echo ""
    echo "❌ 마스터 데이터 import 실패"
    exit 1
fi
