#!/bin/bash

# 가상환경 활성화
source venv/bin/activate

# SQL 쿼리 실행 함수
execute_sql() {
    local query="$1"
    echo "실행 중인 쿼리: $query"
    
    # infisical로 환경변수 주입하여 mysql 실행
    infisical run --env=dev --path=/Backend -- \
    sh -c "
    mysql \
        -h localhost \
        -u root \
        -p\$MYSQL_PASSWORD \
        podpod \
        -e \"$query\"
    "
    if [ $? -eq 0 ]; then
        echo "✅ 쿼리가 성공적으로 실행되었습니다!"
    else
        echo "❌ 쿼리 실행 중 오류가 발생했습니다."
        return 1
    fi
}

# 명령행 인수로 받은 쿼리 실행
if [ $# -eq 0 ]; then
    echo "사용법: $0 \"SQL 쿼리\""
    exit 1
fi

execute_sql "$1"
