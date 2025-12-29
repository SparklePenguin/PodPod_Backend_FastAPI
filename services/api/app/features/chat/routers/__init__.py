"""
Chat routers
"""

from app.features.chat.routers.chat_router import router as chat_router
from app.features.chat.routers.websocket_router import router as websocket_router

__all__ = ["chat_router", "websocket_router"]
