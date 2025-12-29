import os
import sys
from logging.config import fileConfig
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가 (shared 모듈 등을 찾기 위해)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# services/api를 Python 경로에 추가 (app 모듈을 찾기 위해)
services_api_path = project_root / "services" / "api"
sys.path.insert(0, str(services_api_path))

# 모델들이 메타데이터에 등록되도록 명시적으로 import
# 모든 모델을 한 곳에서 import (메타데이터 등록을 위해 필요)
import app.models  # noqa: E402, F401
from alembic import context  # type: ignore  # noqa: E402
from app.core.database import Base  # noqa: E402
from sqlalchemy import engine_from_config, pool  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # MySQL용 동기 엔진 생성
    configuration = config.get_section(config.config_ini_section, {})

    # 환경변수에서 MySQL 설정 가져오기 (./migrate.sh을 통해 주입됨)
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_database: str = os.getenv("MYSQL_DATABASE", "podpod")

    # 필수 환경변수 검증
    if not mysql_password:
        raise ValueError(
            "MYSQL_PASSWORD 환경변수가 설정되지 않았습니다. "
            "Infisical을 사용하여 환경변수를 주입해주세요. "
            "직접 환경변수 설정은 지원되지 않습니다."
        )

    # 비밀번호 URL 인코딩 (latin1로 인코딩 불가한 유니코드 비밀번호 폴백 처리)
    import urllib.parse

    safe_password = mysql_password
    try:
        # latin1로 인코딩 가능하면 그대로 사용
        mysql_password.encode("latin1")
    except UnicodeEncodeError:
        # UTF-8 바이트를 latin1로 재해석하여 PyMySQL에 동일 바이트 전달
        safe_password = mysql_password.encode("utf-8").decode("latin1")

    encoded_password = urllib.parse.quote(safe_password, safe="")

    configuration["sqlalchemy.url"] = (
        f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    )

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
