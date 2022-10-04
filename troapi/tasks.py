from troapi.scheduler import scheduler
from troapi.services import StormService
from troapi.config import SETTINGS

STORMS_MINUTES_UPDATE_INTERVAL = SETTINGS.get("STORMS_MINUTES_UPDATE_INTERVAL", 5)


@scheduler.task(
    "interval",
    id="update_storms",
    minutes=int(STORMS_MINUTES_UPDATE_INTERVAL),
    max_instances=1,
    coalesce=True
)
def update_storms():
    StormService.update_storms()
