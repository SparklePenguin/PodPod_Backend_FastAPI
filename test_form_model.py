"""FastAPI BaseModel에 Form 직접 사용 테스트"""

from fastapi import Form
from pydantic import BaseModel


class TestForm(BaseModel):
    name: str = Form(..., description="이름")
    age: int = Form(..., description="나이")


# 모델이 정상적으로 생성되는지 확인
try:
    test = TestForm(name="test", age=20)
    print("✅ BaseModel 필드에 Form 직접 사용 가능!")
    print(f"   생성된 모델: {test}")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
