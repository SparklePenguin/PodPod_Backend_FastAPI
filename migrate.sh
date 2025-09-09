#!/bin/bash

# 가상환경 활성화
source venv/bin/activate

# 마이그레이션 실행
echo "마이그레이션을 실행 중입니다..."
infisical run --env=dev --path=/backend -- ./venv/bin/alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ 마이그레이션이 성공적으로 완료되었습니다!"
else
    echo "❌ 마이그레이션 실행 중 오류가 발생했습니다."
fi

