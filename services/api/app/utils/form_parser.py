"""
Form 데이터 파싱 유틸리티 함수들
multipart/form-data에서 Pydantic 모델로 변환하는 헬퍼 함수들
"""

import json
from datetime import date, datetime, time
from typing import Any, Dict, List, Type, TypeVar, Union, get_args, get_origin

from fastapi import Request, UploadFile
from fastapi.datastructures import FormData
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class FormParser:
    """Form 데이터를 Pydantic 모델로 파싱하는 유틸리티 클래스"""

    @staticmethod
    async def parse_model_from_form(
        request: Request, model_class: Type[T], json_field_name: str = "data"
    ) -> T:
        """
        multipart/form-data에서 Pydantic 모델로 파싱

        Args:
            request: FastAPI Request 객체
            model_class: 파싱할 Pydantic 모델 클래스
            json_field_name: JSON 데이터가 들어있는 필드명 (기본값: "data")

        Returns:
            파싱된 Pydantic 모델 인스턴스

        Raises:
            RequestValidationError: 파싱 실패 시
        """
        form_data = await request.form()

        # JSON 문자열로 된 필드가 있는지 확인
        if json_field_name in form_data:
            try:
                json_value = form_data[json_field_name]
                # UploadFile이 아닌 str인지 확인
                if isinstance(json_value, str):
                    json_data = json.loads(json_value)
                elif isinstance(json_value, UploadFile):
                    # UploadFile인 경우 읽어서 문자열로 변환
                    content = await json_value.read()
                    json_str = (
                        content.decode("utf-8")
                        if isinstance(content, bytes)
                        else content
                    )
                    json_data = json.loads(json_str)
                else:
                    # 기타 타입은 문자열로 변환 후 파싱
                    json_data = json.loads(str(json_value))
                return model_class(**json_data)
            except (json.JSONDecodeError, ValueError) as e:
                raise RequestValidationError(
                    [
                        {
                            "type": "json_invalid",
                            "loc": ("body", json_field_name),
                            "msg": f"Invalid JSON: {str(e)}",
                        }
                    ]
                )

        # 개별 필드로 파싱 시도
        try:
            parsed_data = FormParser._parse_individual_fields(form_data, model_class)
            return model_class(**parsed_data)
        except (ValueError, TypeError) as e:
            # 더 명확한 오류 메시지 생성
            missing_fields = FormParser._get_missing_fields(form_data, model_class)
            if missing_fields:
                error_msg = f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}"
            else:
                error_msg = f"Invalid form data: {str(e)}"

            raise RequestValidationError(
                [
                    {
                        "type": "value_error",
                        "loc": ("body"),
                        "msg": error_msg,
                    }
                ]
            )

    @staticmethod
    def _parse_individual_fields(
        form_data: FormData, model_class: Type[T]
    ) -> Dict[str, Any]:
        """개별 필드들을 파싱하여 딕셔너리로 변환"""
        parsed_data = {}

        # 모델의 필드 정보 가져오기
        model_fields = model_class.model_fields

        for field_name, field_info in model_fields.items():
            # alias가 있으면 alias로, 없으면 field_name으로 form_data에서 가져오기
            form_field_name = field_info.alias or field_name
            field_value = form_data.get(form_field_name)

            if field_value is None:
                # Optional 필드이고 기본값이 있으면 사용
                if not field_info.is_required():
                    parsed_data[field_name] = field_info.default
                continue

            # 타입에 따른 파싱
            field_type = field_info.annotation
            if field_type is None:
                # 타입이 없으면 문자열로 처리
                parsed_data[field_name] = (
                    str(field_value) if isinstance(field_value, str) else field_value
                )
            else:
                # UploadFile이 아닌 경우에만 파싱
                if isinstance(field_value, str):
                    parsed_data[field_name] = FormParser._parse_field_value(
                        field_value, field_type
                    )
                else:
                    # UploadFile인 경우 그대로 전달
                    parsed_data[field_name] = field_value

        return parsed_data

    @staticmethod
    def _get_missing_fields(form_data: FormData, model_class: Type[T]) -> List[str]:
        """누락된 필수 필드들을 찾아서 반환"""
        missing_fields = []
        model_fields = model_class.model_fields

        for field_name, field_info in model_fields.items():
            # alias가 있으면 alias로, 없으면 field_name으로 form_data에서 가져오기
            form_field_name = field_info.alias or field_name
            field_value = form_data.get(form_field_name)

            # 필수 필드이고 값이 없으면 누락된 필드로 추가
            if field_info.is_required() and (field_value is None or field_value == ""):
                # 클라이언트가 이해하기 쉬운 필드명 사용 (alias 우선)
                display_name = field_info.alias or field_name
                missing_fields.append(display_name)

        return missing_fields

    @staticmethod
    def _parse_field_value(value: str, field_type: type) -> Any:
        """필드 타입에 따라 값을 파싱"""
        if value is None or value == "":
            return None

        # Union 타입 처리 (Optional 포함)
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            # str | None 같은 경우 None을 제외한 타입을 찾음
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                return FormParser._parse_field_value(value, non_none_types[0])
            return str(value)

        # 기본 타입들
        if field_type == str:
            return str(value)
        elif field_type == int:
            return int(value)
        elif field_type == float:
            return float(value)
        elif field_type == bool:
            return value.lower() in ("true", "1", "yes", "on")

        # 날짜/시간 타입들
        elif field_type == date:
            return date.fromisoformat(value)
        elif field_type == time:
            return time.fromisoformat(value)
        elif field_type == datetime:
            return datetime.fromisoformat(value)

        # 리스트 타입 (쉼표로 구분된 문자열)
        elif origin is list:
            if value:
                return [item.strip() for item in value.split(",") if item.strip()]
            return []

        # 기본적으로 문자열로 반환
        return str(value)


# 편의 함수들
async def parse_form_to_model(
    request: Request, model_class: Type[T], json_field_name: str = "data"
) -> T:
    """
    Form 데이터를 Pydantic 모델로 파싱하는 편의 함수

    사용 예시:
        @app.post("/create-pod/")
        async def create_pod(
            request: Request,
            image: UploadFile | None = File(None)
        ):
            req = await parse_form_to_model(request, PodCreateRequest)
            # ... 나머지 로직
    """
    return await FormParser.parse_model_from_form(request, model_class, json_field_name)


async def get_form_field(request: Request, field_name: str, default: Any = None) -> Any:
    """Form에서 특정 필드 값을 가져오는 편의 함수"""
    form_data = await request.form()
    return form_data.get(field_name, default)


async def get_form_file(request: Request, field_name: str) -> UploadFile | None:
    """Form에서 특정 파일을 가져오는 편의 함수"""
    form_data = await request.form()
    file_field = form_data.get(field_name)
    # UploadFile 타입인지 확인
    if isinstance(file_field, UploadFile) and hasattr(file_field, "filename"):
        return file_field
    return None
