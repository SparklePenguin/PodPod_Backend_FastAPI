#!/usr/bin/env python3
"""
Google Sheets ↔ reminders.json 동기화 스크립트

기능:
1. Sheet에서 내용 가져와서 reminders.json 동기화
2. reminders.json에 추가된 리마인더 타입이 있으면 Sheet에 업로드
3. 새 도메인이 추가되면 시트 생성 및 타입 추가

사용법:
    python sync_reminder_types_to_sheet.py

Infisical 환경변수 (자동 로드):
    REMINDER_SHEETS_ID: 리마인더 타입 스프레드시트 ID
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
REMINDERS_JSON_PATH = (
    PROJECT_ROOT / "app" / "core" / "reminders" / "reminders.json"
)

# 시트 헤더
SHEET_HEADERS = [
    "Code",
    "Key",
    "Trigger Hours",
    "Trigger Type",
    "Target",
    "Message Template",
    "Notification Type",
    "Notification Value",
    "Category",
    "Description (ko)",
    "Description (en)",
    "Dev Note",
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


def load_reminders_json() -> dict[str, dict[str, Any]]:
    """reminders.json 파일 로드"""
    if not REMINDERS_JSON_PATH.exists():
        raise FileNotFoundError(
            f"reminders.json 파일을 찾을 수 없습니다: {REMINDERS_JSON_PATH}"
        )

    with open(REMINDERS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"✓ reminders.json 로드 완료 ({len(data)}개 도메인)")
    return data


def save_reminders_json(data: dict[str, dict[str, Any]]) -> None:
    """reminders.json 파일 저장"""
    with open(REMINDERS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✓ reminders.json 저장 완료")


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

    range_name = f"'{sheet_name}'!A1:L1"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": [SHEET_HEADERS]},
    ).execute()


def get_sheet_data(
    service, spreadsheet_id: str, sheet_name: str
) -> dict[str, dict[str, Any]]:
    """시트에서 리마인더 타입 데이터 가져오기"""
    range_name = f"'{sheet_name}'!A:L"

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

    reminder_types = {}
    for i, row in enumerate(values[1:], start=2):
        if len(row) < 10:
            continue

        try:
            reminder_key = row[1].strip()
            reminder_types[reminder_key] = {
                "code": int(row[0].strip()),
                "trigger_hours": int(row[2].strip()) if row[2].strip() else 0,
                "trigger_type": row[3].strip() if len(row) > 3 else "",
                "target": row[4].strip() if len(row) > 4 else "",
                "message_template": row[5].strip() if len(row) > 5 else "",
                "notification_type": row[6].strip() if len(row) > 6 else "",
                "notification_value": row[7].strip() if len(row) > 7 else "",
                "category": row[8].strip() if len(row) > 8 else "",
                "description_ko": row[9].strip() if len(row) > 9 else "",
                "description_en": row[10].strip() if len(row) > 10 else "",
                "dev_note": row[11].strip() if len(row) > 11 else "",
            }
        except (ValueError, IndexError) as e:
            print(f"  ! 행 {i} 파싱 실패: {row}, 오류: {e}")
            continue

    return reminder_types


def append_reminders_to_sheet(
    service,
    spreadsheet_id: str,
    sheet_name: str,
    reminders_to_add: dict[str, dict[str, Any]],
) -> None:
    """시트에 리마인더 타입 추가"""
    if not reminders_to_add:
        return

    rows = []
    for reminder_key, data in reminders_to_add.items():
        rows.append(
            [
                data.get("code", 0),
                reminder_key,
                data.get("trigger_hours", 0),
                data.get("trigger_type", ""),
                data.get("target", ""),
                data.get("message_template", ""),
                data.get("notification_type", ""),
                data.get("notification_value", ""),
                data.get("category", ""),
                data.get("description_ko", ""),
                data.get("description_en", ""),
                data.get("dev_note", ""),
            ]
        )

    range_name = f"'{sheet_name}'!A:L"
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()

    for reminder_key in reminders_to_add:
        print(f"  + Sheet에 추가: {reminder_key}")


def sync_domain(
    service,
    spreadsheet_id: str,
    domain: str,
    json_reminders: dict[str, dict[str, Any]],
    existing_sheets: dict[str, int],
) -> dict[str, dict[str, Any]]:
    """도메인별 동기화 수행"""
    print(f"\n[{domain}]")

    # 시트가 없으면 생성
    if domain not in existing_sheets:
        create_sheet(service, spreadsheet_id, domain)
        append_reminders_to_sheet(service, spreadsheet_id, domain, json_reminders)
        return json_reminders

    # 시트에서 데이터 가져오기
    sheet_reminders = get_sheet_data(service, spreadsheet_id, domain)
    print(f"  Sheet: {len(sheet_reminders)}개, JSON: {len(json_reminders)}개")

    # Sheet → JSON 동기화 (시트가 우선)
    updated_reminders = json_reminders.copy()
    for reminder_key, reminder_data in sheet_reminders.items():
        if reminder_key in updated_reminders:
            # 시트의 주요 필드만 업데이트 (message_template, description 등)
            for field in [
                "message_template",
                "description_ko",
                "description_en",
                "dev_note",
            ]:
                if reminder_data.get(field):
                    updated_reminders[reminder_key][field] = reminder_data[field]
            print(f"  ↓ JSON 업데이트: {reminder_key}")
        else:
            # 시트에만 있는 새 리마인더는 JSON에 추가하지 않음 (개발자가 직접 추가해야 함)
            print(f"  ! 시트에만 존재: {reminder_key} (JSON에 수동 추가 필요)")

    # JSON → Sheet 동기화
    reminders_to_add = {}
    for reminder_key, reminder_data in json_reminders.items():
        if reminder_key not in sheet_reminders:
            reminders_to_add[reminder_key] = reminder_data

    if reminders_to_add:
        append_reminders_to_sheet(service, spreadsheet_id, domain, reminders_to_add)

    return updated_reminders


def main():
    """메인 실행"""
    print("=" * 50)
    print("Google Sheets ↔ reminders.json 동기화")
    print("=" * 50)

    # Infisical에서 환경변수 로드
    load_infisical_secrets()

    spreadsheet_id = os.getenv("REMINDER_SHEETS_ID")
    if not spreadsheet_id:
        print("오류: REMINDER_SHEETS_ID 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    try:
        service = get_google_sheets_service()
        reminders_data = load_reminders_json()

        existing_sheets = get_existing_sheets(service, spreadsheet_id)
        print(f"✓ 기존 시트: {list(existing_sheets.keys())}")

        updated_data = {}
        for domain, domain_reminders in reminders_data.items():
            updated_data[domain] = sync_domain(
                service, spreadsheet_id, domain, domain_reminders, existing_sheets
            )

        save_reminders_json(updated_data)

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
