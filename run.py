#!/usr/bin/env python3
"""
PodPod FastAPI 서버 실행 스크립트

사용법:
    ./run                   # Infisical을 사용하여 실행 (필수)
    ./run --host HOST --port PORT  # 호스트/포트 변경
    ./run --no-reload       # 자동 리로드 비활성화

주의: 이 스크립트는 run 스크립트를 통해 실행되어야 합니다.
Infisical을 통해서만 환경변수를 로드합니다.
"""
import subprocess
import sys
import yaml
from pathlib import Path
import argparse


def load_config():
    """설정 파일에서 서버 설정을 로드합니다."""
    config_file = Path("config.yaml")

    # 기본 설정
    default_config = {
        "server": {
            "host": "127.0.0.1",
            "port": 8000,
            "reload": True,
        },
        "infisical": {
            "enabled": False,
            "env": "dev",
            "path": "/backend",
        },
    }

    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                # 기본 설정과 사용자 설정 병합
                if user_config:
                    default_config.update(user_config)
        except Exception as e:
            print(f"설정 파일 로드 중 오류 발생: {e}")
            print("기본 설정을 사용합니다.")

    return default_config


def check_virtual_env():
    """가상환경이 활성화되어 있는지 확인합니다."""
    return hasattr(sys, "real_prefix") or (
        hasattr(
            sys,
            "base_prefix",
        )
        and sys.base_prefix != sys.prefix
    )


def run_server(config, use_infisical=False):
    """서버를 실행합니다."""
    current_dir = Path.cwd()
    print(f"현재 디렉토리: {current_dir}")

    server_config = config.get("server", {})
    host = server_config.get("host", "127.0.0.1")
    port = server_config.get("port", 8000)
    reload = server_config.get("reload", True)

    print(f"서버 설정: {host}:{port} (reload: {reload})")

    # uvicorn 명령어 구성
    uvicorn_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]

    if reload:
        uvicorn_cmd.append("--reload")

    try:
        if use_infisical:
            infisical_config = config.get("infisical", {})
            env = infisical_config.get(
                "env",
                "dev",
            )

            print("Infisical에서 환경변수를 로드하는 중...")
            # 모든 폴더에서 환경변수 가져오기 (Backend, GoogleSheet 포함)
            cmd = [
                "infisical",
                "run",
                f"--env={env}",
                "--path=/",
                "--recursive",
                "--",
            ] + uvicorn_cmd

            result = subprocess.Popen(
                cmd,
                stdout=sys.stdout,
                stderr=sys.stderr,
                cwd=current_dir,
            )
        else:
            # 이 코드는 실행되지 않음 (Infisical이 항상 사용됨)
            print("❌ 오류: Infisical을 통해서만 서버를 실행할 수 있습니다.")
            print("💡 해결방법: ./run (Infisical 자동 사용)")
            sys.exit(1)

        return result.wait()

    except FileNotFoundError as e:
        if "infisical" in str(e):
            print("Infisical CLI를 찾을 수 없습니다. 설치되어 있는지 확인해주세요.")
        else:
            print(f"명령어를 찾을 수 없습니다: {e}")
        return 1
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="PodPod FastAPI 서버 실행",
    )
    # Infisical은 항상 사용하므로 옵션 제거
    parser.add_argument(
        "--host",
        help="서버 호스트 (기본값: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="서버 포트 (기본값: 8000)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="자동 리로드 비활성화",
    )

    args = parser.parse_args()

    # 설정 로드
    config = load_config()

    # 명령행 인수로 설정 오버라이드
    if args.host:
        config.setdefault(
            "server",
            {},
        )["host"] = args.host
    if args.port:
        config.setdefault(
            "server",
            {},
        )["port"] = args.port
    if args.no_reload:
        config.setdefault(
            "server",
            {},
        )["reload"] = False

    # 가상환경 상태 확인
    if check_virtual_env():
        print("가상환경이 활성화되어 있습니다.")
    else:
        print("가상환경이 활성화되지 않았습니다.")
        print("run 스크립트를 사용하여 실행하세요: ./run")
        return 1

    # Infisical은 항상 사용
    use_infisical = True

    # 서버 실행
    return run_server(
        config,
        use_infisical=use_infisical,
    )


if __name__ == "__main__":
    sys.exit(main())
