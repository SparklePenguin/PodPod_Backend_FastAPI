#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def run_with_infisical():
    """Infisical CLI를 사용해서 환경변수를 로드한 후 애플리케이션을 실행합니다."""

    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"현재 디렉토리: {current_dir}")

    # Infisical CLI로 환경변수 로드
    try:
        print("Infisical에서 환경변수를 로드하는 중...")
        result = subprocess.Popen(
            [
                "infisical",
                "run",
                "--env=dev",
                "--path=/backend",
                "--",
                "python",
                "-m",
                "uvicorn",
                "main:app",
                "--reload",
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd=current_dir,
        )

        if result.returncode != 0:
            print(f"오류 발생: {result.stderr}")
            return result.returncode

        print(result.stdout)
        return 0

    except FileNotFoundError:
        print("Infisical CLI를 찾을 수 없습니다. 설치되어 있는지 확인해주세요.")
        return 1
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_with_infisical())
