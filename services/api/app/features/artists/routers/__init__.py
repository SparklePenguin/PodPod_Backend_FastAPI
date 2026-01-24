from ._base import (
    AritistRootController,
    ArtistSchedulerController,
    ArtistSuggestController
)

# Export for Swagger
from .artist_router import ArtistRouter
from .artist_schedule_router import ArtistScheduleRouter
from .artist_suggestion_router import ArtistSuggestRouter