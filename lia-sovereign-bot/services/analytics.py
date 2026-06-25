from loguru import logger

from config import settings

try:
    from posthog import Posthog
except Exception:  # pragma: no cover - posthog optional
    Posthog = None


class AnalyticsService:
    """PostHog product analytics for LIA bot.

    Полностью опционален: если ключ не задан или библиотека не установлена,
    все вызовы превращаются в no-op и не ломают работу бота.
    """

    def __init__(self) -> None:
        self._client = None
        api_key = ""
        try:
            api_key = settings.posthog_api_key.get_secret_value().strip()
        except Exception:
            api_key = ""

        if not settings.posthog_enabled:
            logger.info("PostHog analytics disabled by config.")
            return
        if not api_key:
            logger.info("PostHog analytics not configured (no API key).")
            return
        if Posthog is None:
            logger.warning("PostHog package not installed — analytics disabled.")
            return

        try:
            self._client = Posthog(
                project_api_key=api_key,
                host=settings.posthog_host,
            )
            logger.info("PostHog analytics initialized.")
        except Exception as e:
            logger.warning(f"PostHog init failed (non-critical): {e}")
            self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def capture(self, user_id: int, event: str, properties: dict | None = None) -> None:
        if not self._client:
            return
        try:
            self._client.capture(
                distinct_id=str(user_id),
                event=event,
                properties=properties or {},
            )
        except Exception as e:
            logger.debug(f"PostHog capture skipped: {e}")

    def identify(self, user_id: int, properties: dict | None = None) -> None:
        if not self._client:
            return
        try:
            self._client.identify(
                distinct_id=str(user_id),
                properties=properties or {},
            )
        except Exception as e:
            logger.debug(f"PostHog identify skipped: {e}")

    def shutdown(self) -> None:
        if not self._client:
            return
        try:
            self._client.shutdown()
        except Exception as e:
            logger.debug(f"PostHog shutdown skipped: {e}")


analytics_service = AnalyticsService()
