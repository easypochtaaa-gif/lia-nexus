"""
LIA Sovereign Bot — HTTP API Server (aiohttp)
Runs on port 8080 alongside the aiogram polling loop.
Provides endpoints for n8n automation workflows.
"""
import hmac
import asyncio
from datetime import datetime, timedelta

from aiohttp import web
from loguru import logger
from sqlalchemy import select, func, text

from config import settings
from database.db import async_session
from database.models import User, Conversation, Threat, Payment

# ── Globals (set from main.py after bot is created) ──
bot_instance = None

# ── Auth ──
def verify_api_key(request: web.Request) -> bool:
    """Check X-API-Key header against configured key."""
    key = request.headers.get("X-API-Key", "")
    expected = settings.n8n_api_key.get_secret_value()
    if not expected:
        return True  # If no key configured, allow all (dev mode)
    return hmac.compare_digest(key, expected)

def require_auth(handler):
    """Decorator: return 401 if API key is invalid."""
    async def wrapper(request: web.Request):
        if not verify_api_key(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        return await handler(request)
    return wrapper

# ── Health ──
async def health(request: web.Request) -> web.Response:
    uptime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return web.json_response({
        "status": "ok",
        "service": "lia-sovereign-bot",
        "timestamp": uptime,
    })

# ── Send Message ──
@require_auth
async def api_send(request: web.Request) -> web.Response:
    """POST /api/send — Send a Telegram message to a specific user.
    Body: {"user_id": 123, "text": "Hello", "parse_mode": "HTML"}"""
    try:
        data = await request.json()
        user_id = int(data["user_id"])
        text = data["text"]
        parse_mode = data.get("parse_mode", "HTML")
    except (KeyError, ValueError, TypeError) as e:
        return web.json_response({"error": f"Invalid body: {e}"}, status=400)

    if not bot_instance:
        return web.json_response({"error": "Bot not ready"}, status=503)

    try:
        msg = await bot_instance.send_message(user_id, text, parse_mode=parse_mode)
        return web.json_response({"ok": True, "message_id": msg.message_id})
    except Exception as e:
        logger.error(f"api_send failed for user {user_id}: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ── Broadcast ──
@require_auth
async def api_broadcast(request: web.Request) -> web.Response:
    """POST /api/broadcast — Send message to all non-banned users.
    Body: {"text": "Announcement", "parse_mode": "HTML"}"""
    try:
        data = await request.json()
        text = data["text"]
        parse_mode = data.get("parse_mode", "HTML")
    except (KeyError, TypeError) as e:
        return web.json_response({"error": f"Invalid body: {e}"}, status=400)

    if not bot_instance:
        return web.json_response({"error": "Bot not ready"}, status=503)

    sent, failed = 0, 0
    async with async_session() as session:
        stmt = select(User.id).where(User.is_banned == False)
        result = await session.execute(stmt)
        user_ids = [row[0] for row in result.all()]

    for uid in user_ids:
        try:
            await bot_instance.send_message(uid, text, parse_mode=parse_mode)
            sent += 1
            await asyncio.sleep(0.05)  # Rate limit: ~20 msg/sec
        except Exception as e:
            failed += 1
            logger.debug(f"Broadcast failed for {uid}: {e}")

    return web.json_response({"ok": True, "total": len(user_ids), "sent": sent, "failed": failed})

# ── User Upgrade ──
@require_auth
async def api_user_upgrade(request: web.Request) -> web.Response:
    """POST /api/user/upgrade — Upgrade/downgrade a user's tier.
    Body: {"user_id": 123, "tier": "pro", "duration_days": 30}"""
    try:
        data = await request.json()
        user_id = int(data["user_id"])
        tier = data["tier"]
        duration_days = int(data.get("duration_days", 30))
    except (KeyError, ValueError, TypeError) as e:
        return web.json_response({"error": f"Invalid body: {e}"}, status=400)

    if tier not in ("free", "lite", "pro", "ultra"):
        return web.json_response({"error": f"Invalid tier: {tier}"}, status=400)

    premium_until = datetime.utcnow() + timedelta(days=duration_days)

    async with async_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return web.json_response({"error": "User not found"}, status=404)

        user.tier = tier
        user.premium_until = premium_until
        await session.commit()

    # Notify the user via Telegram
    tier_labels = {"free": "Free", "lite": "Lite", "pro": "Pro", "ultra": "Ultra"}
    label = tier_labels.get(tier, tier)
    if bot_instance:
        try:
            await bot_instance.send_message(
                user_id,
                f"🎉 <b>STAB IMPERIUM — TIER UPGRADE</b>\n\n"
                f"Твой уровень доступа повышен до: <b>{label}</b>\n"
                f"Действует до: <b>{premium_until.strftime('%Y-%m-%d')}</b>\n\n"
                f"Используй /start чтобы увидеть новые возможности.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Failed to notify user {user_id} of upgrade: {e}")

    logger.info(f"User {user_id} upgraded to {tier} until {premium_until}")
    return web.json_response({
        "ok": True,
        "user_id": user_id,
        "tier": tier,
        "premium_until": premium_until.isoformat(),
    })

# ── Stats ──
async def api_stats(request: web.Request) -> web.Response:
    """GET /api/stats — Pull bot statistics for n8n dashboards/reports."""
    async with async_session() as session:
        # Total users
        total_res = await session.execute(select(func.count(User.id)))
        total_users = total_res.scalar() or 0

        # Users by tier
        tier_res = await session.execute(
            select(User.tier, func.count(User.id)).group_by(User.tier)
        )
        by_tier = {row[0]: row[1] for row in tier_res.all()}

        # Active users today
        today = datetime.utcnow().strftime("%Y-%m-%d")
        active_res = await session.execute(
            select(func.count(User.id)).where(User.last_request_date >= today)
        )
        active_today = active_res.scalar() or 0

        # Total conversations
        conv_res = await session.execute(select(func.count(Conversation.id)))
        total_conversations = conv_res.scalar() or 0

        # Requests today
        reqs_res = await session.execute(
            select(func.sum(User.daily_requests)).where(User.last_request_date >= today)
        )
        requests_today = reqs_res.scalar() or 0

        # Threats (30 days)
        from services.aegis_shield import get_threat_count, get_threat_breakdown, get_critical_threats
        total_threats = await get_threat_count(30)
        critical_threats = await get_critical_threats(30)
        threat_breakdown = await get_threat_breakdown(30)

        # Premium users
        premium_until_res = await session.execute(
            select(func.count(User.id)).where(User.premium_until > datetime.utcnow())
        )
        premium_active = premium_until_res.scalar() or 0

    return web.json_response({
        "ok": True,
        "users": {
            "total": total_users,
            "active_today": active_today,
            "by_tier": by_tier,
            "premium_active": premium_active,
        },
        "activity": {
            "requests_today": requests_today,
            "total_conversations": total_conversations,
        },
        "security": {
            "threats_30d": total_threats,
            "critical_threats_30d": critical_threats,
            "breakdown": threat_breakdown,
        },
    })

# ── User Info ──
@require_auth
async def api_user_info(request: web.Request) -> web.Response:
    """GET /api/user/{user_id} — Query user details."""
    user_id = int(request.match_info["user_id"])

    async with async_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return web.json_response({"error": "User not found"}, status=404)

        return web.json_response({
            "ok": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "tier": user.tier,
                "premium_until": user.premium_until.isoformat() if user.premium_until else None,
                "daily_requests": user.daily_requests,
                "total_requests": user.total_requests,
                "referrals_count": user.referrals_count,
                "bonus_requests": user.bonus_requests,
                "xp": user.xp,
                "stab_coins": user.stab_coins,
                "aegis_score": user.aegis_score,
                "is_banned": user.is_banned,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_active": user.last_active.isoformat() if user.last_active else None,
            }
        })

# ── App Factory ──
def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/api/health", health)
    app.router.add_post("/api/send", api_send)
    app.router.add_post("/api/broadcast", api_broadcast)
    app.router.add_post("/api/user/upgrade", api_user_upgrade)
    app.router.add_get("/api/stats", api_stats)
    app.router.add_get("/api/user/{user_id}", api_user_info)
    logger.info("HTTP API routes registered")
    return app
