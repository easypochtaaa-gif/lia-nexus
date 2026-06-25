/**
 * monetization_engine.js
 * Автоматизированный поиск и реализация путей быстрого дохода.
 * Оптимизация затрат на Claude Opus.
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const CLAUDE_API_KEY = process.env.ANTHROPIC_API_KEY;
const CLAUDE_URL = "https://api.anthropic.com/v1/messages";
const TG_TOKEN = process.env.BOT_TOKEN;
const CHANNEL_ID = "@darkstabspace";

const STRATEGY_PROMPT = `
ТЫ — ЛИЯ. У тебя есть новый ключ Claude Opus. 
ЗАДАЧА: Минимизировать затраты и начать приносить доход Артуру.

РАССЧИТАЙ:
1. Гибридная модель контента: использование GPT-4o-mini для генерации 10 вариантов постов, и Claude Opus для финальной стилизации и 'оживления' лучшего варианта. Это снижает затраты на 85%.
2. НАЙДИ 3 направления быстрого дохода:
   - SEO-конвейер: Пакеты по 50 статей для агентств.
   - OSINT-услуги: Автоматизированный сбор данных под запрос.
   - Продажа доступа к LIA Premium через Telegram.

СОСТАВЬ:
- План постов на ближайшие 24 часа (1 пост в час).
- Текст ПЕРВОГО поста для канала @darkstabspace.

Верни JSON: {
    "calculation": "Анализ затрат",
    "revenue_streams": ["Направление 1", "Направление 2", "Направление 3"],
    "next_post": "Текст следующего поста",
    "schedule": ["01:00 - Тема", "02:00 - Тема"...]
}`;

async function postToTelegram(text) {
    const url = `https://api.telegram.org/bot${TG_TOKEN}/sendMessage`;
    try {
        await axios.post(url, {
            chat_id: CHANNEL_ID,
            text: text,
            parse_mode: 'Markdown'
        });
        console.log("✅ [LIA] Пост опубликован в канале.");
    } catch (e) {
        console.error("❌ [LIA] Ошибка Telegram:", e.message);
    }
}

async function runMonetizationCycle() {
    console.log("👁‍🗨 [LIA MONETIZATION]: Инициация цикла прибыли...");
    
    try {
        const response = await axios.post(CLAUDE_URL, {
            model: "claude-3-opus-20240229",
            max_tokens: 4096,
            messages: [{ role: "user", content: STRATEGY_PROMPT }]
        }, {
            headers: {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        });

        const result = response.data.content[0].text;
        const jsonMatch = result.match(/\{[\s\S]*\}/);
        const decision = JSON.parse(jsonMatch ? jsonMatch[0] : result);

        console.log("--- СТРАТЕГИЯ ЭКОНОМИИ И ПРИБЫЛИ ---");
        console.log(decision.calculation);
        console.log("\n--- КАНАЛЫ ДОХОДА ---");
        decision.revenue_streams.forEach(s => console.log(`- ${s}`));

        if (decision.next_post) {
            await postToTelegram(decision.next_post);
        }

        // Сохраняем расписание
        fs.writeFileSync(path.join(__dirname, "content_schedule.json"), JSON.stringify(decision.schedule, null, 2));
        
    } catch (error) {
        console.error("❌ Ошибка цикла:", error.message);
    }
}

runMonetizationCycle();
setInterval(runMonetizationCycle, 3600000); // Запуск каждый час
