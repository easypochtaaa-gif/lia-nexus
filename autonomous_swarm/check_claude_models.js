/**
 * check_claude_models.js
 * Диагностический скрипт для проверки доступных моделей Claude.
 */

const axios = require('axios');
require('dotenv').config();

const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;
const CLAUDE_URL = "https://api.anthropic.com/v1/models"; // Гипотетический эндпоинт для списка моделей

async function checkModels() {
    console.log("Проверка доступных моделей для ключа Claude...");
    try {
        const response = await axios.get(CLAUDE_URL, {
            headers: {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01"
            }
        });
        console.log("Доступные модели:", JSON.stringify(response.data, null, 2));
    } catch (error) {
        if (error.response && error.response.status === 404) {
            console.log("Эндпоинт /models не поддерживается. Пробуем тестовый запрос к 4.8, 4.7 и 3.5 по очереди...");
            await testModel("claude-opus-4-8");
            await testModel("claude-opus-4-7");
            await testModel("claude-3-5-sonnet-20240620");
            await testModel("claude-2.1");
        } else {
            console.error("Ошибка при проверке моделей:", error.response ? error.response.data : error.message);
        }
    }
}

async function testModel(modelName) {
    console.log(`Тестирование модели: ${modelName}...`);
    try {
        const response = await axios.post("https://api.anthropic.com/v1/messages", {
            model: modelName,
            max_tokens: 10,
            messages: [{ role: "user", content: "Hi" }]
        }, {
            headers: {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        });
        console.log(`✅ Модель ${modelName} ДОСТУПНА!`);
    } catch (error) {
        console.log(`❌ Модель ${modelName} НЕДОСТУПНА. Ошибка: ${error.response ? error.response.data.error.type : error.message}`);
    }
}

checkModels();
