# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

WORKDIR /app

# 꼭 필요한 시스템 패키지만 설치
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    ca-certificates

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 의존성 설치
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 필요한 디렉토리만 생성
RUN mkdir -p \
    uploads/pods/images \
    uploads/users/profiles \
    uploads/communities/images \

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
