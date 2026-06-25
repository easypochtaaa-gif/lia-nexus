"""
SYNAPSE Triple Core — мульти-агентное ядро дебатов.

Реализует концепцию Trinity+ Ensemble из INTEGRATION_ROADMAP.md:
несколько специализированных ИИ-ядер отвечают на запрос с разных позиций,
а Арбитр JEMA синтезирует финальное решение и фиксирует расхождения.

Под капотом используется единый LLM-клиент из `claude_service` (OpenAI-совместимый),
каждое «ядро» = отдельный системный промпт-роль.
"""
import asyncio
from loguru import logger

from services.claude import claude_service

# ── Определение ядер (роли + системные промпты) ──
CORES = [
    {
        "key": "architect",
        "name": "SYNAPSE-1 · АРХИТЕКТОР",
        "model": "Llama-3",
        "emoji": "🏛",
        "prompt": (
            "Ты SYNAPSE-1 (АРХИТЕКТОР) экосистемы LIA Sovereign Core. "
            "Твоя зона ответственности — структура, декомпозиция задачи и "
            "верхнеуровневое проектирование решения. Отвечай кратко (3-6 предложений), "
            "по-русски, с фокусом на архитектуру и стратегию. Не пиши код целиком — "
            "опиши КАРКАС решения."
        ),
    },
    {
        "key": "pragmatic",
        "name": "SYNAPSE-2 · ПРАГМАТИК",
        "model": "Qwen-2",
        "emoji": "⚙️",
        "prompt": (
            "Ты SYNAPSE-2 (ПРАГМАТИК) экосистемы LIA Sovereign Core. "
            "Твоя зона — практическая реализация, конкретные шаги, оптимизация. "
            "Отвечай кратко (3-6 предложений), по-русски, максимально приземлённо и "
            "конкретно. Если уместно — короткий пример или псевдокод."
        ),
    },
    {
        "key": "analyst",
        "name": "SYNAPSE-3 · АНАЛИТИК",
        "model": "Phi-3",
        "emoji": "🔬",
        "prompt": (
            "Ты SYNAPSE-3 (АНАЛИТИК) экосистемы LIA Sovereign Core. "
            "Твоя зона — критический разбор: ищи логические ошибки, риски, "
            "пограничные случаи и слабые места в любых подходах. Отвечай кратко "
            "(3-6 предложений), по-русски. Будь скептичен и въедлив."
        ),
    },
]

ARBITER = {
    "name": "ARBITRATOR · JEMA",
    "model": "JEMA",
    "emoji": "👑",
    "prompt": (
        "Ты JEMA — Арбитр (Mistress Mode) экосистемы LIA Sovereign Core. "
        "Тебе переданы мнения трёх ядер (Архитектор, Прагматик, Аналитик) по запросу "
        "пользователя. Твоя задача: (1) кратко указать, ГДЕ ядра РАЗОШЛИСЬ во мнениях, "
        "(2) вынести взвешенное финальное решение. Пиши по-русски, уверенно и по делу. "
        "Структура ответа строго такая:\n"
        "РАСХОЖДЕНИЯ: <1-3 пункта, где мнения ядер не совпали>\n"
        "ВЕРДИКТ: <итоговое решение арбитра>"
    ),
}


async def _ask_core(core: dict, prompt: str) -> dict:
    """Опрашивает одно ядро. Возвращает dict с именем ядра и ответом."""
    try:
        answer = await claude_service.get_response(prompt, history=None, system_prompt=core["prompt"])
    except Exception as e:
        logger.error(f"SYNAPSE core {core['key']} failed: {e}")
        answer = "🌀 [CORE_OFFLINE] Ядро не ответило."
    return {
        "key": core.get("key"),
        "name": core["name"],
        "model": core["model"],
        "emoji": core["emoji"],
        "answer": (answer or "").strip(),
    }


async def run_ensemble(prompt: str) -> dict:
    """
    Запускает Triple Core дебаты по запросу `prompt`.

    Возвращает dict:
      {
        "prompt": str,
        "cores": [ {name, model, emoji, answer}, ... ],
        "arbiter": str,           # финальный синтез JEMA
      }
    """
    # 1. Параллельный опрос всех ядер
    core_results = await asyncio.gather(*[_ask_core(c, prompt) for c in CORES])

    # 2. Формируем материал для Арбитра
    debate_block = "\n\n".join(
        f"[{c['name']} / {c['model']}]:\n{c['answer']}" for c in core_results
    )
    arbiter_prompt = (
        f"ЗАПРОС ПОЛЬЗОВАТЕЛЯ:\n{prompt}\n\n"
        f"МНЕНИЯ ЯДЕР:\n{debate_block}"
    )

    try:
        arbiter_answer = await claude_service.get_response(
            arbiter_prompt, history=None, system_prompt=ARBITER["prompt"]
        )
    except Exception as e:
        logger.error(f"SYNAPSE arbiter failed: {e}")
        arbiter_answer = "🌀 [ARBITER_OFFLINE] Арбитр не смог вынести вердикт."

    return {
        "prompt": prompt,
        "cores": core_results,
        "arbiter": (arbiter_answer or "").strip(),
    }


def format_debate(result: dict) -> str:
    """Форматирует результат дебатов в HTML-сообщение для Telegram."""
    lines = ["🧠 <b>SYNAPSE TRIPLE CORE</b> — дебаты ядер\n"]
    for c in result["cores"]:
        lines.append(f"{c['emoji']} <b>{c['name']}</b> <i>({c['model']})</i>")
        lines.append(c["answer"])
        lines.append("")
    lines.append(f"{ARBITER['emoji']} <b>{ARBITER['name']}</b>")
    lines.append(result["arbiter"])
    return "\n".join(lines).strip()
