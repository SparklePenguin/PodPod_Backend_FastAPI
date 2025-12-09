#!/bin/bash

# 마스터 데이터 import 스크립트
# seeds/master_data.sql 파일을 대상 환경의 DB에 적용

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "📥 마스터 데이터 import"
echo ""

# 마스터 데이터 파일 확인
MASTER_DATA_FILE="seeds/master_data.sql"

if [ ! -f "$MASTER_DATA_FILE" ]; then
    echo -e "${RED}❌ 마스터 데이터 파일을 찾을 수 없습니다: $MASTER_DATA_FILE${NC}"
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

# 환경 선택
echo "🌍 대상 환경을 선택하세요:"
echo "  1) dev    - 개발 환경 (Docker 컨테이너)"
echo "  2) stg    - 스테이징 환경 (로컬 MySQL)"
echo "  3) custom - 직접 입력"
echo ""

read -p "선택 (1-3): " ENV_CHOICE

case $ENV_CHOICE in
    1)
        ENV="dev"
        echo ""
        echo -e "${BLUE}📦 개발 환경 (Docker) 선택${NC}"
        echo ""

        # Docker 컨테이너 확인
        if ! docker ps | grep -q "podpod-mysql-dev"; then
            echo -e "${YELLOW}⚠️  podpod-mysql-dev 컨테이너가 실행 중이지 않습니다.${NC}"
            echo "먼저 ./scripts/start-dev.sh 를 실행하세요."
            exit 1
        fi

        read -sp "MySQL root password: " MYSQL_PASSWORD
        echo ""
        echo ""

        echo "🔄 데이터 import 중..."
        docker exec -i podpod-mysql-dev mysql -u root -p"$MYSQL_PASSWORD" podpod_dev < "$MASTER_DATA_FILE"

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ 개발 환경에 마스터 데이터 import 완료!${NC}"
        else
            echo ""
            echo -e "${RED}❌ Import 실패${NC}"
            exit 1
        fi
        ;;

    2)
        ENV="stg"
        echo ""
        echo -e "${BLUE}🚀 스테이징 환경 선택${NC}"
        echo ""

        read -p "Database host (기본: localhost): " DB_HOST
        DB_HOST=${DB_HOST:-localhost}

        read -p "Database port (기본: 3306): " DB_PORT
        DB_PORT=${DB_PORT:-3306}

        read -p "Database name (기본: podpod_staging): " DB_NAME
        DB_NAME=${DB_NAME:-podpod_staging}

        read -p "Database user (기본: root): " DB_USER
        DB_USER=${DB_USER:-root}

        read -sp "Database password: " DB_PASSWORD
        echo ""
        echo ""

        echo "🔄 데이터 import 중..."
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$MASTER_DATA_FILE"

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ 스테이징 환경에 마스터 데이터 import 완료!${NC}"
        else
            echo ""
            echo -e "${RED}❌ Import 실패${NC}"
            exit 1
        fi
        ;;

    3)
        echo ""
        echo -e "${BLUE}⚙️  사용자 정의 설정${NC}"
        echo ""

        read -p "Database host: " DB_HOST
        read -p "Database port (기본: 3306): " DB_PORT
        DB_PORT=${DB_PORT:-3306}
        read -p "Database name: " DB_NAME
        read -p "Database user: " DB_USER
        read -sp "Database password: " DB_PASSWORD
        echo ""
        echo ""

        echo "🔄 데이터 import 중..."
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$MASTER_DATA_FILE"

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ 마스터 데이터 import 완료!${NC}"
        else
            echo ""
            echo -e "${RED}❌ Import 실패${NC}"
            exit 1
        fi
        ;;

    *)
        echo -e "${RED}❌ 잘못된 선택입니다.${NC}"
        exit 1
        ;;
esac

echo ""
