"""
Google Sheets에서 에러 코드를 가져오는 서비스
"""

import os
import json
from typing import Dict, List, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings
from app.core.http_status import HttpStatus


class GoogleSheetsService:
    def __init__(self):
        self.service = None
        self.spreadsheet_id = None
        self.range_name = None

    async def initialize(self, spreadsheet_id: str, range_name: str = "ErrorCodes!A:E"):
        """Google Sheets 서비스 초기화"""
        try:
            # 환경변수에서 JSON 문자열로 인증 시도
            credentials_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

            if credentials_json:
                # 환경변수에서 JSON 문자열로 인증
                import json

                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
                )
                print("Google Sheets API 초기화 완료: 환경변수에서 인증")
            else:
                # 파일에서 인증 (기존 방식)
                credentials_path = os.getenv(
                    "GOOGLE_CREDENTIALS_PATH", "credentials.json"
                )

                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        f"Google 서비스 계정 키 파일을 찾을 수 없습니다: {credentials_path}"
                    )

                # 서비스 계정 인증
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
                )
                print(f"Google Sheets API 초기화 완료: {credentials_path}")

            # Google Sheets API 서비스 빌드
            self.service = build("sheets", "v4", credentials=credentials)
            self.spreadsheet_id = spreadsheet_id

            # 시트 이름에 공백이 있으면 따옴표로 감싸기
            if "!" in range_name:
                sheet_name, range_part = range_name.split("!", 1)
                if " " in sheet_name and not (
                    sheet_name.startswith("'") and sheet_name.endswith("'")
                ):
                    self.range_name = f"'{sheet_name}'!{range_part}"
                else:
                    self.range_name = range_name
            else:
                self.range_name = range_name

        except Exception as e:
            raise Exception(f"Google Sheets 서비스 초기화 실패: {str(e)}")

    async def get_error_codes(self) -> Dict[str, Dict[str, Any]]:
        """Google Sheets에서 모든 시트의 에러 코드 데이터를 가져옵니다"""
        if not self.service:
            raise Exception("Google Sheets 서비스가 초기화되지 않았습니다")

        try:
            # 먼저 시트 목록을 가져옵니다
            result = (
                self.service.spreadsheets()
                .get(spreadsheetId=self.spreadsheet_id)
                .execute()
            )

            sheets = result.get("sheets", [])
            all_error_codes = {}

            # 각 시트에서 에러 코드를 가져옵니다
            for sheet in sheets:
                sheet_properties = sheet.get("properties", {})
                sheet_name = sheet_properties.get("title", "")

                # 시트 이름이 에러 코드 시트인지 확인 (1xxx, 2xxx, 3xxx, 4xxx, 5xxx로 시작)
                if not any(
                    sheet_name.startswith(prefix)
                    for prefix in ["1xxx", "2xxx", "3xxx", "4xxx", "5xxx"]
                ):
                    continue

                print(f"시트 '{sheet_name}'에서 에러 코드를 가져오는 중...")

                try:
                    # 시트 이름에 공백이 있으면 따옴표로 감싸기
                    if " " in sheet_name and not (
                        sheet_name.startswith("'") and sheet_name.endswith("'")
                    ):
                        range_name = f"'{sheet_name}'!A:F"
                    else:
                        range_name = f"{sheet_name}!A:F"

                    # 시트에서 데이터 가져오기
                    sheet_result = (
                        self.service.spreadsheets()
                        .values()
                        .get(spreadsheetId=self.spreadsheet_id, range=range_name)
                        .execute()
                    )

                    values = sheet_result.get("values", [])
                    if not values:
                        print(
                            f"경고: 시트 '{sheet_name}'에서 데이터를 찾을 수 없습니다"
                        )
                        continue

                    # 헤더 행 (첫 번째 행) - PodPod Error 시트 형식
                    headers = values[0]
                    expected_headers = [
                        "Code",
                        "Key",
                        "HTTP Status",
                        "Message (ko)",
                        "Message (en)",
                        "해결 가이드 (dev note)",
                    ]

                    # 헤더 검증
                    if headers != expected_headers:
                        print(
                            f"경고: 시트 '{sheet_name}'의 헤더 형식이 올바르지 않습니다. 예상: {expected_headers}, 실제: {headers}"
                        )
                        continue

                    # 데이터 파싱
                    sheet_error_codes = {}
                    for i, row in enumerate(values[1:], start=2):  # 헤더 제외하고 시작
                        if len(row) < len(expected_headers):
                            print(
                                f"경고: 시트 '{sheet_name}' {i}번째 행의 데이터가 불완전합니다: {row}"
                            )
                            continue

                        try:
                            code = int(row[0].strip())
                            error_key = row[1].strip()
                            http_status = int(row[2].strip())
                            message_ko = row[3].strip()
                            message_en = row[4].strip()
                            dev_note = row[5].strip() if len(row) > 5 else None

                            # HTTP 상태 코드 검증
                            if http_status not in [200, 201, 400, 401, 403, 404, 500]:
                                print(
                                    f"경고: {error_key}의 HTTP 상태 코드가 유효하지 않습니다: {http_status}"
                                )
                                continue

                            sheet_error_codes[error_key] = {
                                "code": code,
                                "http_status": http_status,
                                "message_ko": message_ko,
                                "message_en": message_en,
                                "dev_note": dev_note,
                            }

                        except (ValueError, IndexError) as e:
                            print(
                                f"경고: 시트 '{sheet_name}' {i}번째 행 파싱 실패: {row}, 오류: {str(e)}"
                            )
                            continue

                    # 중복 키 확인
                    for key, value in sheet_error_codes.items():
                        if key in all_error_codes:
                            print(
                                f"경고: 에러 키 '{key}'가 중복됩니다. 시트 '{sheet_name}'의 값으로 덮어씁니다."
                            )
                        all_error_codes[key] = value

                    print(
                        f"시트 '{sheet_name}'에서 {len(sheet_error_codes)}개의 에러 코드를 가져왔습니다."
                    )

                except Exception as e:
                    print(
                        f"경고: 시트 '{sheet_name}'에서 에러 코드를 가져오는 중 오류 발생: {str(e)}"
                    )
                    continue

            print(f"총 {len(all_error_codes)}개의 에러 코드를 가져왔습니다.")
            return all_error_codes

        except HttpError as e:
            raise Exception(f"Google Sheets API 오류: {str(e)}")
        except Exception as e:
            raise Exception(f"에러 코드 데이터 가져오기 실패: {str(e)}")

    async def get_error_codes_from_file(
        self, file_path: str
    ) -> Dict[str, Dict[str, Any]]:
        """로컬 JSON 파일에서 에러 코드를 가져옵니다 (백업용)"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"로컬 에러 코드 파일 읽기 실패: {str(e)}")

    def validate_error_codes(self, error_codes: Dict[str, Dict[str, Any]]) -> List[str]:
        """에러 코드 데이터의 유효성을 검증합니다"""
        errors = []

        for error_key, error_data in error_codes.items():
            # 필수 필드 검증
            required_fields = ["code", "http_status", "message_ko", "message_en"]
            for field in required_fields:
                if field not in error_data:
                    errors.append(f"{error_key}: 필수 필드 '{field}'가 없습니다")

            # 코드 범위 검증
            if "code" in error_data:
                code = error_data["code"]
                if not (1000 <= code <= 9999):
                    errors.append(
                        f"{error_key}: 코드가 유효한 범위(1000-9999)를 벗어났습니다: {code}"
                    )

            # HTTP 상태 코드 검증
            if "http_status" in error_data:
                http_status = error_data["http_status"]
                valid_statuses = [200, 201, 400, 401, 403, 404, 500]
                if http_status not in valid_statuses:
                    errors.append(
                        f"{error_key}: HTTP 상태 코드가 유효하지 않습니다: {http_status}"
                    )

        return errors


# 전역 인스턴스
google_sheets_service = GoogleSheetsService()
