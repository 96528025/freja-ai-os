import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import Settings
from app.db.session import SessionLocal
from app.repositories.asset_repository import AssetRepository
from app.services.brief_service import BriefGenerationInProgress, BriefService

logger = logging.getLogger(__name__)


class FrejaScheduler:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.scheduler = AsyncIOScheduler(timezone=settings.timezone)

    async def generate_if_missing_today(self) -> None:
        local_now = datetime.now(ZoneInfo(self.settings.timezone))
        scheduled_time = local_now.replace(
            hour=self.settings.brief_hour,
            minute=self.settings.brief_minute,
            second=0,
            microsecond=0,
        )
        if local_now < scheduled_time:
            return
        with SessionLocal() as session:
            if AssetRepository(session).latest_brief_today(self.settings.timezone):
                return
            try:
                await BriefService(session, self.settings).generate()
            except BriefGenerationInProgress:
                logger.info("Brief generation already running; scheduled run skipped")
            except Exception:
                logger.exception("Scheduled brief generation failed")

    def start(self) -> None:
        self.scheduler.add_job(
            self.generate_if_missing_today,
            "cron",
            hour=self.settings.brief_hour,
            minute=self.settings.brief_minute,
            id="daily-ai-brief",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=86_400,
        )
        startup_check = datetime.now(ZoneInfo(self.settings.timezone)) + timedelta(seconds=1)
        self.scheduler.add_job(
            self.generate_if_missing_today,
            "date",
            run_date=startup_check,
            id="startup-brief-catch-up",
            replace_existing=True,
        )
        self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
