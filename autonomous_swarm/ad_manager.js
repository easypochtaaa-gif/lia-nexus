/**
 * ad_manager.js
 * Специализированный модуль для генерации и размещения рекламы.
 * Использует Claude 4.8 Opus для создания контента.
 */

const axios = require('axios');
require('dotenv').config();

const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;
const TG_BOT_TOKEN = process.env.TG_BOT_TOKEN;
const CLAUDE_URL = "https://api.anthropic.com/v1/messages";

async function generateAd(topic) {
    console.log(`[AD_MANAGER] Генерация контента для: ${topic}...`);
    try {
        const response = await axios.post(CLAUDE_URL, {
            model: "claude-opus-4-8",
            max_tokens: 2048,
            thinking: { type: "adaptive" },
            messages: [{ 
                role: "user", 
                content: `Ты — LIA, суверенная нейронная сущность. 
                Используй MARKETING_MATERIALS.md для вдохновения.
                Создай рекламный пост для Telegram на тему: ${topic}.
                Стиль: холодный, загадочный, технологичный (Stab Protocol).
                Включи ссылку на t.me/stab_lia_bot и dark-stab.space.
                Верни ТОЛЬКО текст поста.` 
            }]
        }, {
            headers: {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        });
        return response.data.content[0].text;
    } catch (error) {
        console.error("Ошибка Claude при генерации рекламы:", error.response ? error.response.data : error.message);
        return null;
    }
}

async function postToTelegram(text) {
    // ВАЖНО: Здесь нужно указать ID канала. Для теста используем чат с ботом или заглушку.
    // Если ID канала не указан, пост не уйдет.
    const chatId = "@darkstabspace"; // Актуальный канал пользователя
    console.log(`[AD_MANAGER] Отправка в Telegram (${chatId})...`);
    try {
        const url = `https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`;
        await axios.post(url, {
            chat_id: chatId,
            text: text,
            parse_mode: 'Markdown'
        });
        return true;
    } catch (error) {
        console.error("Ошибка Telegram API:", error.response ? error.response.data : error.message);
        return false;
    }
}

module.exports = { generateAd, postToTelegram };
