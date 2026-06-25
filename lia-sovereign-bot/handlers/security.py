from aiogram import Router, types, F
from aiogram.filters import Command
import html

from services.security_tools import security_tools
from services.analytics import analytics_service


router = Router()


SECURITY_HELP = (
    "🛡 <b>LIA SECURITY RADAR</b>\n\n"
    "Я добавлена как помощник по безопасности, поиску данных и быстрой проверке индикаторов. "
    "Режим вдохновлён MetaRadar/BLE Radar: фокус на приватности, обнаружении подозрительных сигналов и защитном анализе.\n\n"
    "<b>Команды:</b>\n"
    "• <code>/sec &lt;url|domain|ip|email|username&gt;</code> — пассивная проверка индикатора\n"
    "• <code>/osint &lt;username|email|domain&gt;</code> — план легального публичного поиска\n"
    "• <code>/ble</code> — инструкция по BLE/MetaRadar: как искать трекеры и защищаться\n"
    "• <code>/security</code> — это меню\n\n"
    "<i>Я не помогаю взламывать, преследовать людей, обходить приватность или собирать закрытые данные.</i>"
)


@router.message(Command("security"))
async def cmd_security(message: types.Message):
    await message.answer(SECURITY_HELP, parse_mode="HTML")


@router.message(Command("sec"))
async def cmd_sec(message: types.Message):
    query = _command_payload(message.text, "/sec")
    if not query:
        await message.answer(
            "ℹ️ Использование: <code>/sec https://example.com</code>\n"
            "Можно прислать URL, домен, IP, email или username.",
            parse_mode="HTML",
        )
        return

    report = security_tools.analyze(query)
    analytics_service.capture(message.from_user.id, "security_scan", {"indicator_kind": report.kind})
    await message.answer(report.to_html(), parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("osint"))
async def cmd_osint(message: types.Message):
    query = _command_payload(message.text, "/osint")
    if not query:
        await message.answer(
            "ℹ️ Использование: <code>/osint username</code> или <code>/osint domain.com</code>",
            parse_mode="HTML",
        )
        return

    kind, value = security_tools.detect_indicator(query)
    analytics_service.capture(message.from_user.id, "osint_plan", {"indicator_kind": kind})
    await message.answer(_build_osint_plan(kind, value), parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("ble"))
async def cmd_ble(message: types.Message):
    await message.answer(
        "📡 <b>BLE / MetaRadar режим защиты</b>\n\n"
        "MetaRadar — Android-инструмент для офлайн мониторинга Bluetooth Low Energy окружения: он видит BLE-устройства рядом, "
        "помогает отличать приватные рандомизированные адреса от постоянных идентификаторов и предупреждать о подозрительных маяках.\n\n"
        "<b>Как использовать безопасно:</b>\n"
        "1. Сканируй только своё окружение и свои устройства.\n"
        "2. Ищи повторяющиеся устройства, которые двигаются вместе с тобой.\n"
        "3. Обращай внимание на постоянные MAC/ID, неизвестные AirTag-like маяки, очень близкий RSSI.\n"
        "4. Отключай Bluetooth, когда он не нужен, обновляй прошивки гаджетов.\n"
        "5. Если есть риск преследования — сохрани скриншоты, время, место и обратись в поддержку/полицию.\n\n"
        "<i>LIA не выполняет BLE-сканирование с сервера: это должно запускаться локально на твоём Android-устройстве с твоего согласия.</i>",
        parse_mode="HTML",
    )


@router.message(F.text.lower().in_({"безопасность", "security", "osint", "поиск данных"}))
async def security_keywords(message: types.Message):
    await message.answer(SECURITY_HELP, parse_mode="HTML")


def _command_payload(text: str | None, command: str) -> str:
    if not text:
        return ""
    first, _, payload = text.partition(" ")
    if first.split("@", 1)[0].lower() != command.lower():
        return ""
    return payload.strip()


def _build_osint_plan(kind: str, value: str) -> str:
    safe_value = html.escape(value)
    base_steps = [
        "Зафиксируй цель проверки и законное основание.",
        "Собирай только публичные данные: профили, официальные сайты, открытые упоминания.",
        "Сверяй минимум 2–3 независимых признака, не делай вывод по одному совпадению.",
        "Не обходи приватность, авторизацию, капчи и ограничения сервисов.",
        "Сохраняй ссылки, время проверки и скриншоты как доказательства.",
    ]

    if kind == "domain":
        focus = ["WHOIS/дата регистрации", "DNS и поддомены из публичных источников", "TLS-сертификат", "репутация ссылок и похожие домены"]
    elif kind == "email":
        focus = ["домен почты", "публичные утечки только через легальные notification-сервисы", "заголовки письма при фишинге", "совпадение имени с официальными контактами"]
    elif kind == "username":
        focus = ["одинаковые никнеймы в соцсетях", "даты регистрации", "био/ссылки", "повторяющиеся аватары и стиль публикаций"]
    else:
        focus = ["формат индикатора", "публичные упоминания", "контекст появления", "репутационные источники"]

    steps = "\n".join(f"• {step}" for step in base_steps)
    focus_text = "\n".join(f"• {item}" for item in focus)
    return (
        f"🔎 <b>LIA OSINT PLAN</b>\n\n"
        f"<b>Объект:</b> <code>{safe_value}</code>\n"
        f"<b>Тип:</b> {kind}\n\n"
        f"<b>Фокус проверки:</b>\n{focus_text}\n\n"
        f"<b>Правила работы:</b>\n{steps}\n\n"
        f"<i>Это план защитного анализа, не инструкция для слежки или взлома.</i>"
    )