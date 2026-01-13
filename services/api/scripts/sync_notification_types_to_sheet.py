#!/usr/bin/env python3
"""
Google Sheets ↔ Notification Events 동기화 스크립트

기능:
1. 코드의 NotificationEvent enum에서 이벤트 목록을 가져옴
2. Google Sheets와 동기화 (새 이벤트 추가, 삭제된 이벤트 제거)
3. Sheet 데이터를 notifications.json으로 저장
4. 서버는 notifications.json을 로드하여 알림 메시지 렌더링에 사용

데이터 흐름:
    NotificationEvent enum → Google Sheets ↔ notifications.json → 서버 런타임

컬럼 구조 (Source of Truth: Google Sheets):
- Category: 알림 카테고리 [코드에서 자동 설정 - EVENT_CATEGORY_MAP]
- Event: 이벤트 이름 [코드에서 자동 설정 - NotificationEvent enum]
- Meta: 메타 정보 (is_reminder 등) [시트 관리]
- Ref: 사용할 Ref 타입 [시트 관리]
- Message Template: 메시지 템플릿 [시트 관리]
- Target: 알림 대상 [시트 관리]
- Description: 설명 [시트 관리]
- Dev Note: 개발 노트 [시트 관리]

Ref별 사용 가능한 Placeholder:
- PodRef: [party_name], [pod_id]
- UserRef: [nickname], [user_id]
- ReviewRef: [review_id]

새 이벤트 추가 시:
1. NotificationEvent enum에 새 이벤트 추가
2. EVENT_CATEGORY_MAP에 카테고리 매핑 추가
3. 이 스크립트 실행 → 시트에 빈 행 추가됨
4. 시트에서 Meta, Ref, Message Template 등 채우기
5. 스크립트 다시 실행 → notifications.json 업데이트

사용법:
    cd services/api
    python scripts/sync_notification_types_to_sheet.py

Infisical 환경변수 (자동 로드):
    NOTIFICATION_SHEETS_ID: 알림 타입 스프레드시트 ID
    GOOGLE_SHEETS_CREDENTIALS: Google 서비스 계정 JSON
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

# 프로젝트 루트 설정
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
APP_ROOT = PROJECT_ROOT / "app"
NOTIFICATIONS_JSON_PATH = APP_ROOT / "core" / "notifications" / "notifications.json"

# Python path에 app 추가
sys.path.insert(0, str(PROJECT_ROOT))

from app.features.notifications.category import NotificationCategory  # noqa: E402
from app.features.notifications.category_map import EVENT_CATEGORY_MAP  # noqa: E402
from app.features.notifications.event import NotificationEvent  # noqa: E402

# 시트 설정
SHEET_NAME = "Notifications"
SHEET_HEADERS = [
    "Category",
    "Event",
    "Meta",
    "Ref",
    "Message Template",
    "Target",
    "Description",
    "Dev Note",
]

# Ref별 사용 가능한 Placeholder
REF_PLACEHOLDERS = {
    "PodRef": ["party_name", "pod_id"],
    "UserRef": ["nickname", "user_id"],
    "ReviewRef": ["review_id"],
}

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


def build_default_event_data() -> list[dict[str, Any]]:
    """코드에서 기본 이벤트 데이터 구성 (새 이벤트용 빈 값)"""
    events_data = []

    for event in NotificationEvent:
        category = EVENT_CATEGORY_MAP.get(event, NotificationCategory.SYSTEM)

        events_data.append(
            {
                "category": category.value,
                "event": event.value,
                "meta": "",  # 시트에서 관리
                "ref": "",  # 시트에서 관리
                "message_template": "",  # 시트에서 관리
                "target": "",  # 시트에서 관리
                "description": "",  # 시트에서 관리
                "dev_note": "",  # 시트에서 관리
            }
        )

    return events_data


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

    # 헤더 추가
    range_name = f"'{sheet_name}'!A1:{chr(65 + len(SHEET_HEADERS) - 1)}1"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": [SHEET_HEADERS]},
    ).execute()


def get_sheet_data(
    service, spreadsheet_id: str, sheet_name: str
) -> dict[str, dict[str, Any]]:
    """시트에서 이벤트 데이터 가져오기 (Event를 key로)"""
    range_name = f"'{sheet_name}'!A:H"

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

    events_data = {}
    for i, row in enumerate(values[1:], start=2):
        if len(row) < 2:
            continue

        try:
            event_key = row[1].strip() if len(row) > 1 else ""
            if not event_key:
                continue

            events_data[event_key] = {
                "category": row[0].strip() if len(row) > 0 else "",
                "event": event_key,
                "meta": row[2].strip() if len(row) > 2 else "",
                "ref": row[3].strip() if len(row) > 3 else "",
                "message_template": row[4].strip() if len(row) > 4 else "",
                "target": row[5].strip() if len(row) > 5 else "",
                "description": row[6].strip() if len(row) > 6 else "",
                "dev_note": row[7].strip() if len(row) > 7 else "",
            }
        except (ValueError, IndexError) as e:
            print(f"  ! 행 {i} 파싱 실패: {row}, 오류: {e}")
            continue

    return events_data


def update_sheet_data(
    service,
    spreadsheet_id: str,
    sheet_name: str,
    events_data: list[dict[str, Any]],
) -> None:
    """시트 전체 데이터 업데이트 (헤더 포함)"""
    # 헤더 행 업데이트 (row 1)
    header_range = f"'{sheet_name}'!A1:{chr(65 + len(SHEET_HEADERS) - 1)}1"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=header_range,
        valueInputOption="RAW",
        body={"values": [SHEET_HEADERS]},
    ).execute()

    # 기존 데이터 클리어 (row 2 이후)
    range_name = f"'{sheet_name}'!A2:H1000"
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range_name,
    ).execute()

    # 새 데이터 작성
    rows = []
    for data in events_data:
        rows.append(
            [
                data.get("category", ""),
                data.get("event", ""),
                data.get("meta", ""),
                data.get("ref", ""),
                data.get("message_template", ""),
                data.get("target", ""),
                data.get("description", ""),
                data.get("dev_note", ""),
            ]
        )

    if rows:
        range_name = f"'{sheet_name}'!A2:H{len(rows) + 1}"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body={"values": rows},
        ).execute()


def save_notifications_json(events_data: list[dict[str, Any]]) -> None:
    """notifications.json 파일 저장"""
    # JSON 구조 생성
    notifications = {}

    for data in events_data:
        event_key = data.get("event", "")
        if not event_key:
            continue

        # Ref에서 placeholders 추출
        refs = [r.strip() for r in data.get("ref", "").split(",") if r.strip()]
        placeholders = []
        for ref in refs:
            placeholders.extend(REF_PLACEHOLDERS.get(ref, []))

        # related_id_type 추론
        related_id_type = "pod_id"  # 기본값
        if "ReviewRef" in refs:
            related_id_type = "review_id"
        elif "UserRef" in refs and "PodRef" not in refs:
            related_id_type = "user_id"

        notifications[event_key] = {
            "category": data.get("category", ""),
            "message_template": data.get("message_template", ""),
            "placeholders": list(set(placeholders)),  # 중복 제거
            "related_id_type": related_id_type,
            "meta": {
                "is_reminder": "is_reminder" in data.get("meta", ""),
            },
            "ref": refs,
            "target": data.get("target", ""),
            "description": data.get("description", ""),
        }

    # JSON 파일 저장
    with open(NOTIFICATIONS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(notifications, f, ensure_ascii=False, indent=2)

    print(f"✓ notifications.json 저장 완료 ({len(notifications)}개 이벤트)")
    print(f"  경로: {NOTIFICATIONS_JSON_PATH}")


def sync_events(
    service,
    spreadsheet_id: str,
    existing_sheets: dict[str, int],
) -> list[dict[str, Any]]:
    """이벤트 데이터 동기화"""
    print(f"\n[{SHEET_NAME}]")

    # 코드에서 기본 이벤트 데이터 빌드
    default_events = build_default_event_data()
    default_events_map = {e["event"]: e for e in default_events}
    print(f"  코드에서 {len(default_events)}개 이벤트 로드")

    # 시트가 없으면 생성하고 기본값 업로드
    if SHEET_NAME not in existing_sheets:
        create_sheet(service, spreadsheet_id, SHEET_NAME)
        update_sheet_data(service, spreadsheet_id, SHEET_NAME, default_events)
        print(f"  + {len(default_events)}개 이벤트 추가 (기본값)")
        return default_events

    # 시트에서 기존 데이터 가져오기
    sheet_events = get_sheet_data(service, spreadsheet_id, SHEET_NAME)
    print(f"  시트에서 {len(sheet_events)}개 이벤트 로드")

    # 병합: 시트 데이터 우선, 새 이벤트는 기본값 사용
    merged_events = []
    for event in NotificationEvent:
        event_key = event.value
        default_data = default_events_map.get(event_key, {})
        sheet_data = sheet_events.get(event_key, {})

        if sheet_data:
            # 시트 데이터가 있으면 시트 우선 (Category만 코드에서)
            merged = {
                "category": default_data.get("category", ""),
                "event": event_key,
                # 나머지는 시트 데이터 사용
                "meta": sheet_data.get("meta", ""),
                "ref": sheet_data.get("ref", ""),
                "message_template": sheet_data.get("message_template", ""),
                "target": sheet_data.get("target", ""),
                "description": sheet_data.get("description", ""),
                "dev_note": sheet_data.get("dev_note", ""),
            }
        else:
            # 새 이벤트는 기본값 사용
            merged = default_data.copy()
            print(f"  + 새 이벤트 추가: {event_key}")

        merged_events.append(merged)

    # 시트 업데이트
    update_sheet_data(service, spreadsheet_id, SHEET_NAME, merged_events)

    # 변경 사항 출력
    added = set(default_events_map.keys()) - set(sheet_events.keys())
    removed = set(sheet_events.keys()) - set(default_events_map.keys())

    if added:
        print(f"  + 추가된 이벤트: {len(added)}개")
    if removed:
        print(f"  - 제거된 이벤트: {', '.join(sorted(removed))}")
    if not added and not removed:
        print("  = 이벤트 목록 변경 없음")

    # 구현 필요한 이벤트 확인 (Message Template이 비어있는 경우)
    incomplete_events = [
        e for e in merged_events
        if not e.get("message_template", "").strip()
    ]

    return merged_events, incomplete_events


def main():
    """메인 실행"""
    print("=" * 60)
    print("Google Sheets ↔ Notification Events 동기화")
    print("=" * 60)
    print("\n📋 Ref별 사용 가능한 Placeholder:")
    for ref, placeholders in REF_PLACEHOLDERS.items():
        print(f"   {ref}: {', '.join(f'[{p}]' for p in placeholders)}")

    # Infisical에서 환경변수 로드
    load_infisical_secrets()

    # 환경변수 확인
    spreadsheet_id = os.getenv("NOTIFICATION_SHEETS_ID")
    if not spreadsheet_id:
        print("오류: NOTIFICATION_SHEETS_ID 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    try:
        service = get_google_sheets_service()

        existing_sheets = get_existing_sheets(service, spreadsheet_id)
        print(f"✓ 기존 시트: {list(existing_sheets.keys())}")

        # 시트 동기화
        merged_events, incomplete_events = sync_events(
            service, spreadsheet_id, existing_sheets
        )

        # notifications.json 저장
        save_notifications_json(merged_events)

        # 구현 필요한 이벤트 표시
        if incomplete_events:
            print(f"\n⚠️  구현 필요한 이벤트: {len(incomplete_events)}개")
            print("   (Message Template이 비어있음 - 시트에서 채워주세요)")
            for event in incomplete_events:
                print(f"   - {event['event']}")

        print("\n" + "=" * 60)
        if incomplete_events:
            print(f"✅ 동기화 완료! (구현 필요: {len(incomplete_events)}개)")
        else:
            print("✅ 동기화 완료!")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"오류: {e}")
        sys.exit(1)
    except HttpError as e:
        print(f"Google API 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"오류: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
