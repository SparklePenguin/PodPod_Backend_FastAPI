"""Pydantic v2 마이그레이션: alias를 serialization_alias로 변경"""

import re
from pathlib import Path


def fix_alias_in_file(file_path: Path) -> tuple[bool, int]:
    """파일에서 alias를 serialization_alias로 변경"""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Field(..., serialization_alias="xxx") -> Field(..., serialization_alias="xxx")
        # validation_alias는 제외
        pattern = r"Field\((.*?),\s*alias="

        def replace_alias(match):
            prefix = match.group(1)
            return f"Field({prefix}, serialization_alias="

        content = re.sub(pattern, replace_alias, content)

        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            changes = content.count("serialization_alias=") - original_content.count(
                "serialization_alias="
            )
            return True, changes
        return False, 0

    except Exception as e:
        print(f"❌ 오류 ({file_path}): {e}")
        return False, 0


# 모든 Python 파일에서 alias 수정
project_root = Path(".")
changed_files = []
total_changes = 0

# Grep 결과에서 찾은 파일들 처리
files_to_fix = [
    "app/features/pods/schemas/pod_create_request.py",
    "app/features/pods/routers/recruitment_router.py",
    "app/features/auth/services/kakao_oauth_service.py",
    "app/features/follow/schemas/follow.py",
    "app/features/users/schemas.py",
    "app/features/pods/schemas/pod_image_dto.py",
    "app/features/pods/schemas/review_schemas.py",
    "app/features/pods/schemas/pod_detail_dto.py",
    "app/features/pods/schemas/pod_like_dto.py",
    "app/features/pods/schemas/pod_review.py",
    "app/features/pods/schemas/pod_dto.py",
    "app/features/artists/schemas/artist_suggestion_schemas.py",
    "app/features/artists/schemas/artist_suggestion.py",
    "app/features/artists/schemas/artist.py",
    "app/features/artists/schemas/artist_sync_dto.py",
    "app/features/artists/schemas/artist_name.py",
    "app/features/artists/schemas/artist_image.py",
    "app/features/artists/schemas/artist_schemas.py",
    "app/features/artists/schemas/artist_unit.py",
    "app/features/notifications/repositories/notification_repository.py",
    "app/api/v1/endpoints/health.py",
    "app/api/v1/endpoints/admin/fcm.py",
    "app/api/v1/endpoints/sessions.py",
    "app/features/notifications/schemas/notification.py",
    "app/features/auth/services/google_oauth_service.py",
    "app/features/auth/services/apple_oauth_service.py",
    "app/api/v1/endpoints/pod/recruitments.py",
    "app/features/tendencies/schemas/tendency.py",
    "app/features/tendencies/schemas.py",
    "app/features/users/schemas/random_profile_image.py",
    "app/features/auth/routers/session_router.py",
    "app/features/pods/schemas/pod_member_dto.py",
    "app/features/pods/schemas/pod_application_dto.py",
    "app/features/pods/schemas/simple_application_dto.py",
    "app/features/artists/schemas/artist_schedule_schemas.py",
    "app/features/locations/schemas.py",
    "app/features/auth/schemas/auth.py",
    "app/features/locations/schemas/location_dto.py",
    "app/features/artists/schemas/artist_schedule.py",
]

for file_path_str in files_to_fix:
    file_path = project_root / file_path_str
    if file_path.exists():
        changed, count = fix_alias_in_file(file_path)
        if changed:
            changed_files.append(file_path_str)
            total_changes += count
            print(f"✅ {file_path_str}: {count}개 변경")

print(f"\n📊 총 {len(changed_files)}개 파일에서 {total_changes}개 수정 완료")
