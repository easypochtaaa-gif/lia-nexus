"""
🛡 AEGIS SHIELD — Real security threat logger.
Logs and counts actual security events: bans, spam, floods,
admin access denials, API abuse, rate limits, auth failures.
"""
from datetime import datetime
from sqlalchemy import select, func
from loguru import logger

from database.db import async_session
from database.models import Threat


THREAT_TYPES = {
    "ban": "Пользователь забанен",
    "spam": "Спам-атака",
    "flood": "Флуд (быстрые сообщения)",
    "rate_limit": "Превышен лимит запросов",
    "admin_deny": "Отказ в админ-доступе",
    "auth_fail": "Неудачная попытка входа",
    "suspicious": "Подозрительная активность",
    "scan": "AEGIS-сканирование завершено",
}

THREAT_SEVERITY = {
    "ban": "high",
    "spam": "medium",
    "flood": "medium",
    "rate_limit": "low",
    "admin_deny": "high",
    "auth_fail": "medium",
    "suspicious": "medium",
    "scan": "low",
}


async def log_threat(
    threat_type: str,
    user_id: int = None,
    source: str = None,
    details: str = None,
    severity: str = None,
    blocked: bool = True,
):
    """Log a security event to the threats table. Also pushes high/critical threats to n8n."""
    if threat_type not in THREAT_TYPES:
        logger.warning(f"Unknown threat type: {threat_type}")
        return

    sev = severity or THREAT_SEVERITY.get(threat_type, "medium")

    async with async_session() as session:
        threat = Threat(
            user_id=user_id,
            threat_type=threat_type,
            severity=sev,
            source=source,
            details=details,
            blocked=blocked,
            created_at=datetime.utcnow(),
        )
        session.add(threat)
        await session.commit()
        label = THREAT_TYPES.get(threat_type, threat_type)
        logger.info(f"🛡 AEGIS: [{sev.upper()}] {label}" + (f" | user={user_id}" if user_id else "") + (f" | {details}" if details else ""))

    # Push high/critical threats to n8n webhook for escalation
    if sev in ("high", "critical"):
        await _notify_n8n_threat(threat_type, user_id, sev, source, details)


async def _notify_n8n_threat(
    threat_type: str,
    user_id: int,
    severity: str,
    source: str,
    details: str,
):
    """Send threat alert to n8n webhook for automated escalation."""
    import aiohttp
    from config import settings

    n8n_url = f"{settings.n8n_url}/webhook/aegis-threat-alert"
    webhook_token = settings.n8n_webhook_token.get_secret_value()

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "threat_type": threat_type,
                "user_id": user_id,
                "severity": severity,
                "source": source,
                "details": details,
                "label": THREAT_TYPES.get(threat_type, threat_type),
            }
            headers = {}
            if webhook_token:
                headers["X-API-Key"] = webhook_token
            await session.post(
                n8n_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            )
            logger.debug(f"Threat pushed to n8n: [{severity}] {threat_type}")
    except Exception as e:
        logger.warning(f"Failed to notify n8n of threat: {e}")


async def get_threat_count(days: int = 30) -> int:
    """Get total threats in the last N days."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    async with async_session() as session:
        stmt = select(func.count(Threat.id)).where(Threat.created_at >= cutoff)
        result = await session.execute(stmt)
        return result.scalar() or 0


async def get_threat_breakdown(days: int = 30) -> dict:
    """Get threat count broken down by type."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    async with async_session() as session:
        stmt = (
            select(Threat.threat_type, func.count(Threat.id))
            .where(Threat.created_at >= cutoff)
            .group_by(Threat.threat_type)
        )
        result = await session.execute(stmt)
        rows = result.all()
        return {row[0]: row[1] for row in rows}


async def get_critical_threats(days: int = 30) -> int:
    """Get count of high/critical severity threats."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    async with async_session() as session:
        stmt = (
            select(func.count(Threat.id))
            .where(Threat.created_at >= cutoff)
            .where(Threat.severity.in_(["high", "critical"]))
        )
        result = await session.execute(stmt)
        return result.scalar() or 0
