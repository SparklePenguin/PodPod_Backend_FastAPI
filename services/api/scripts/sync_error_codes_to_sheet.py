#!/usr/bin/env python3
"""
Google Sheets ↔ errors.json 동기화 스크립트

기능:
1. Sheet에서 내용 가져와서 errors.json 동기화
2. errors.json에 추가된 에러 케이스가 있으면 Sheet에 업로드
3. 새 도메인이 추가되면 시트 생성 및 케이스 추가

사용법:
    python sync_error_codes_to_sheet.py

Infisical 환경변수 (자동 로드):
    GOOGLE_SHEETS_ID: 스프레드시트 ID
    GOOGLE_SHEETS_CREDENTIALS: Google 서비스 계정 JSON (문자열)
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 프로젝트 루트 경로
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ERRORS_JSON_PATH = PROJECT_ROOT / "app" / "core" / "errors.json"

# 시트 헤더
SHEET_HEADERS = [
    "Code",
    "Key",
    "HTTP Status",
    "Message (ko)",
    "Message (en)",
    "해결 가이드 (dev note)",
]


def load_infisical_secrets() -> None:
    """Infisical에서 환경변수 로드"""
    try:
        result = subprocess.run(
            [
                "infisical",
                "export",
                "--path",
                "/google-sheet",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        secrets = json.loads(result.stdout)
        for secret in secrets:
            key = secret.get("key")
            value = secret.get("value")
            if key and value:
                os.environ[key] = value

        print("✓ Infisical 환경변수 로드 완료 (path: /google-sheet)")

    except subprocess.CalledProcessError as e:
        print(f"! Infisical 로드 실패: {e.stderr}")
        print("  기존 환경변수를 사용합니다.")
    except FileNotFoundError:
        print("! Infisical CLI가 설치되지 않았습니다.")
        print("  기존 환경변수를 사용합니다.")
    except json.JSONDecodeError:
        print("! Infisical 출력 파싱 실패")
        print("  기존 환경변수를 사용합니다.")


def get_google_sheets_service():
    """Google Sheets API 서비스 생성 (읽기/쓰기 권한)"""
    credentials_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

    if credentials_json:
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        print("✓ Google Sheets API 인증 완료")
    else:
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"인증 파일을 찾을 수 없습니다: {credentials_path}")

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        print(f"✓ Google Sheets API 인증 완료 ({credentials_path})")

    return build("sheets", "v4", credentials=credentials)


def load_errors_json() -> dict[str, dict[str, Any]]:
    """errors.json 파일 로드"""
    if not ERRORS_JSON_PATH.exists():
        raise FileNotFoundError(
            f"errors.json 파일을 찾을 수 없습니다: {ERRORS_JSON_PATH}"
        )

    with open(ERRORS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"✓ errors.json 로드 완료 ({len(data)}개 도메인)")
    return data


def save_errors_json(data: dict[str, dict[str, Any]]) -> None:
    """errors.json 파일 저장"""
    with open(ERRORS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✓ errors.json 저장 완료")


def get_existing_sheets(service, spreadsheet_id: str) -> dict[str, int]:
    """기존 시트 목록 가져오기 (시트명: 시트ID)"""
    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = {}
    for sheet in result.get("sheets", []):
        props = sheet.get("properties", {})
        sheets[props.get("title", "")] = props.get("sheetId", 0)
    return sheets


def create_sheet(service, spreadsheet_id: str, sheet_name: str) -> None:
    """새 시트 생성 및 헤더 추가"""
    request = {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": sheet_name,
                    }
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=request
    ).execute()
    print(f"  + 시트 생성: {sheet_name}")

    range_name = f"'{sheet_name}'!A1:F1"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": [SHEET_HEADERS]},
    ).execute()


def get_sheet_data(
    service, spreadsheet_id: str, sheet_name: str
) -> dict[str, dict[str, Any]]:
    """시트에서 에러 코드 데이터 가져오기"""
    range_name = f"'{sheet_name}'!A:F"

    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
    except HttpError as e:
        print(f"  ! 시트 '{sheet_name}' 읽기 실패: {e}")
        return {}

    values = result.get("values", [])
    if len(values) <= 1:
        return {}

    error_codes = {}
    for i, row in enumerate(values[1:], start=2):
        if len(row) < 5:
            continue

        try:
            error_key = row[1].strip()
            error_codes[error_key] = {
                "code": int(row[0].strip()),
                "http_status": int(row[2].strip()),
                "message_ko": row[3].strip(),
                "message_en": row[4].strip(),
                "dev_note": row[5].strip() if len(row) > 5 else "",
            }
        except (ValueError, IndexError) as e:
            print(f"  ! 행 {i} 파싱 실패: {row}, 오류: {e}")
            continue

    return error_codes


def append_errors_to_sheet(
    service,
    spreadsheet_id: str,
    sheet_name: str,
    errors_to_add: dict[str, dict[str, Any]],
) -> None:
    """시트에 에러 코드 추가"""
    if not errors_to_add:
        return

    rows = []
    for error_key, error_data in errors_to_add.items():
        rows.append(
            [
                error_data.get("code", 0),
                error_key,
                error_data.get("http_status", 400),
                error_data.get("message_ko", ""),
                error_data.get("message_en", ""),
                error_data.get("dev_note", ""),
            ]
        )

    range_name = f"'{sheet_name}'!A:F"
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()

    for error_key in errors_to_add:
        print(f"  + Sheet에 추가: {error_key}")


def sync_domain(
    service,
    spreadsheet_id: str,
    domain: str,
    json_errors: dict[str, dict[str, Any]],
    existing_sheets: dict[str, int],
) -> dict[str, dict[str, Any]]:
    """도메인별 동기화 수행"""
    print(f"\n[{domain}]")

    # 시트가 없으면 생성
    if domain not in existing_sheets:
        create_sheet(service, spreadsheet_id, domain)
        append_errors_to_sheet(service, spreadsheet_id, domain, json_errors)
        return json_errors

    # 시트에서 데이터 가져오기
    sheet_errors = get_sheet_data(service, spreadsheet_id, domain)
    print(f"  Sheet: {len(sheet_errors)}개, JSON: {len(json_errors)}개")

    # Sheet → JSON 동기화
    updated_errors = json_errors.copy()
    for error_key, error_data in sheet_errors.items():
        if error_key in updated_errors:
            updated_errors[error_key] = error_data
            print(f"  ↓ JSON 업데이트: {error_key}")
        else:
            updated_errors[error_key] = error_data
            print(f"  ↓ JSON에 추가: {error_key}")

    # JSON → Sheet 동기화
    errors_to_add = {}
    for error_key, error_data in json_errors.items():
        if error_key not in sheet_errors:
            errors_to_add[error_key] = error_data

    if errors_to_add:
        append_errors_to_sheet(service, spreadsheet_id, domain, errors_to_add)

    return updated_errors


def main():
    """메인 실행"""
    print("=" * 50)
    print("Google Sheets ↔ errors.json 동기화")
    print("=" * 50)

    # Infisical에서 환경변수 로드
    load_infisical_secrets()

    # 환경변수 확인
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not spreadsheet_id:
        print("오류: GOOGLE_SHEETS_ID 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    try:
        service = get_google_sheets_service()
        errors_data = load_errors_json()

        existing_sheets = get_existing_sheets(service, spreadsheet_id)
        print(f"✓ 기존 시트: {list(existing_sheets.keys())}")

        updated_data = {}
        for domain, domain_errors in errors_data.items():
            updated_data[domain] = sync_domain(
                service, spreadsheet_id, domain, domain_errors, existing_sheets
            )

        save_errors_json(updated_data)

        print("\n" + "=" * 50)
        print("동기화 완료!")
        print("=" * 50)

    except FileNotFoundError as e:
        print(f"오류: {e}")
        sys.exit(1)
    except HttpError as e:
        print(f"Google API 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
