"""
Admin routers
"""

from app.features.admin.routers.error_codes import router as error_codes_router
from app.features.admin.routers.fcm import router as fcm_router
from app.features.admin.routers.sendbird import router as sendbird_router

__all__ = ["error_codes_router", "fcm_router", "sendbird_router"]
