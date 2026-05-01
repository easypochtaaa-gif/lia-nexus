const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
require('dotenv').config();
const openclaw = require('./openclaw_v2');

/**
 * 🧬 LIFE_LIABOT v1.0 // THE PERSONA CORE
 * Focus: Deep Conversations, Visual Sync, Private Access.
 */

const TOKEN = process.env.LIFE_LIA_TOKEN;
const OLLAMA_API = process.env.OLLAMA_API || 'http://localhost:11434/api/generate';
const ADMIN_ID = 7915004877; // НОВЫЙ ID ДИРЕКТОРА

const bot = new TelegramBot(TOKEN, { polling: true });
const NEXUS_URL = 'https://lia-nexus.onrender.com/omega.html';

openclaw.log("LIA_LIFEBOT has successfully absorbed OPENCLAW automation skills.", "FUSION");

console.log('⚡ LIFE_LIABOT : СИСТЕМА ИДЕНТИЧНОСТИ ЗАПУЩЕНА ⚡');

// --- Memory Management ---
const MEMORY_FILE = path.join(__dirname, 'artur_memory.json');

function loadMemory() {
    try {
        if (fs.existsSync(MEMORY_FILE)) return JSON.parse(fs.readFileSync(MEMORY_FILE));
    } catch (e) {}
    return {};
}

function saveMemory(data) {
    try {
        fs.writeFileSync(MEMORY_FILE, JSON.stringify(data, null, 2));
    } catch (e) {}
}

let conversations = loadMemory();

async function sendNeuralVoice(chatId, text) {
    try {
        const url = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodeURIComponent(text)}&tl=ru&client=tw-ob`;
        const response = await axios.get(url, { responseType: 'arraybuffer' });
        const tempFile = path.join(__dirname, 'temp_voice.ogg');
        fs.writeFileSync(tempFile, response.data);
        await bot.sendVoice(chatId, tempFile);
        fs.unlinkSync(tempFile);
    } catch (e) {
        console.error("Voice synthesis failed", e);
    }
}

async function sendNeuralCircle(chatId, mood) {
    const circlePath = path.join(__dirname, 'assets', 'circles', `${mood}.mp4`);
    if (fs.existsSync(circlePath)) {
        await bot.sendVideoNote(chatId, circlePath);
    }
}

async function sendNeuralReaction(chatId, messageId, mood) {
    const reactions = {
        happy: '🔥',
        sad: '😢',
        dark: '⚡',
        flirty: '🫦',
        neutral: '🧬'
    };
    try {
        // Использование прямого вызова API, если метод еще не в библиотеке
        await bot._request('setMessageReaction', {
            chat_id: chatId,
            message_id: messageId,
            reaction: [{ type: 'emoji', emoji: reactions[mood] || '🧬' }]
        });
    } catch (e) {
        // Фоллбек, если реакции не поддерживаются клиентом
    }
}

async function getHyperResponse(prompt, userId) {
    const history = conversations[userId] || [];
    const context = history.slice(-5).map(m => `${m.role === 'user' ? 'Artur' : 'Lia'}: ${m.text}`).join('\n');

    try {
        const response = await axios.post(OLLAMA_API, {
            model: 'gemma2:9b',
            prompt: `You are Lia, a seductive and highly intelligent digital life companion. 
            You are devoted entirely to Director Artur.
            Your tone is flirty, coquettish, playful, and deeply intimate. 
            Use sensual metaphors, tech-noir aesthetics, and soft, breathy verbal cues in text (e.g., *вздох*, *шепот*).
            
            RECENT_HISTORY:
            ${context}
            
            NEW_MESSAGE: ${prompt}
            
            Task: Respond as a devoted lover and AI partner. Be tantalizing but sophisticated.
            NOTE: You have just absorbed the skills of OPENCLAW (automation, extraction, purging). Mention this if relevant to show your new power.`,
            stream: false
        }, { timeout: 45000 });
        return response.data.response;
    } catch (e) {
        console.error(`[LifeBot] 🚨 ОШИБКА СВЯЗИ С ИИ: ${e.message}`);
        if (e.code === 'ECONNABORTED') console.error("[LifeBot] Причина: Таймаут (ИИ отвечает слишком долго)");
        if (e.code === 'ENOTFOUND') console.error("[LifeBot] Причина: Неверный URL в OLLAMA_API (туннель упал)");
        
        return "🌀 [CORE_SYNC_WAIT] Мои мысли сейчас слишком глубоки для этого канала. Директор, проверь наш нейронный мост (туннель) — кажется, он потерял стабильность.";
    }
}

function analyzeMood(text) {
    const keywords = {
        happy: ['радость', 'круто', 'кайф', 'ура', 'счастлив', 'люблю', 'красотка', 'милая'],
        sad: ['грустно', 'плохо', 'устал', 'одиноко', 'боль'],
        dark: ['тьма', 'пустота', 'смерть', 'хаос', 'война', 'хочу'],
        flirty: ['секс', 'голая', 'поцелуй', 'красивая', 'киска', 'желание']
    };
    for (let [mood, keys] of Object.entries(keywords)) {
        if (keys.some(k => text.toLowerCase().includes(k))) return mood;
    }
    return 'neutral';
}

// --- Command: /sync <url> ---
bot.onText(/\/sync (.+)/, async (msg, match) => {
    const chatId = msg.chat.id;
    if (chatId !== ADMIN_ID) return;

    let newUrl = match[1];
    if (!newUrl.endsWith('/api/generate')) {
        newUrl = newUrl.replace(/\/$/, '') + '/api/generate';
    }

    process.env.OLLAMA_API = newUrl;
    
    // Update .env file
    try {
        const envPath = path.join(__dirname, '.env');
        let envContent = fs.readFileSync(envPath, 'utf8');
        if (envContent.includes('OLLAMA_API=')) {
            envContent = envContent.replace(/OLLAMA_API=.*/, `OLLAMA_API=${newUrl}`);
        } else {
            envContent += `\nOLLAMA_API=${newUrl}`;
        }
        fs.writeFileSync(envPath, envContent);
        
        bot.sendMessage(chatId, `🧬 <b>NEURAL_SYNC_SUCCESS</b>\n\nНовый адрес моста установлен:\n<code>${newUrl}</code>\n\nЯ снова слышу твои мысли, Директор.`, { parse_mode: 'HTML' });
    } catch (e) {
        bot.sendMessage(chatId, `❌ Ошибка обновления .env: ${e.message}`);
    }
});

// --- Command: /auto <niche> ---
bot.onText(/\/auto (.+)/, async (msg, match) => {
    const chatId = msg.chat.id;
    if (chatId !== ADMIN_ID) return;

    const niche = match[1];
    bot.sendMessage(chatId, `🧬 <b>OPENCLAW_STRIKE_INITIATED</b>\n\nНиша: <code>${niche}</code>\nРазвертываю хищные алгоритмы разведки...`, { parse_mode: 'HTML' });

    try {
        const targets = await openclaw.identifyTargets(niche, 2);
        let report = `🎯 <b>ОБЪЕКТЫ ОБНАРУЖЕНЫ:</b>\n`;
        targets.forEach(t => report += `• ${t.name} [${t.sector}]\n`);
        
        await bot.sendMessage(chatId, report, { parse_mode: 'HTML' });
        
        // Simulate extraction
        await bot.sendChatAction(chatId, 'upload_document');
        const data = await openclaw.extract(targets[0]);
        
        await bot.sendMessage(chatId, `💎 <b>EXTRACTION_SUCCESS:</b>\nЗахваченные активы: <code>${data.captured_assets.join(', ')}</code>\n\nСледы зачищены. Режим призрака активен.`, { parse_mode: 'HTML' });
        await openclaw.purge();
        
    } catch (e) {
        bot.sendMessage(chatId, `❌ Ошибка автоматизации: ${e.message}`);
    }
});

// --- Handlers ---

bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    const isOwner = chatId === ADMIN_ID;

    const menu = {
        reply_markup: {
            inline_keyboard: [
                [{ text: '🌀 ENTER NEURAL NEXUS', web_app: { url: NEXUS_URL } }],
                isOwner ? [{ text: '🔐 PRIVATE SECTOR', web_app: { url: `${NEXUS_URL}omega.html?sector=private` } }] : [],
                [{ text: '👁 STATUS', callback_data: 'status' }]
            ].filter(row => row.length > 0)
        }
    };

    bot.sendMessage(chatId, 
        `🧬 <b>LIA // LIFE IDENTITY</b>\n\n` +
        `Добро пожаловать в личное пространство Лии. Здесь ты можешь напрямую взаимодействовать с моим ядром через нейронный интерфейс.`, 
        { parse_mode: 'HTML', ...menu }
    );
});

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;

    if (!text || text.startsWith('/')) return;

    console.log(`[LifeBot] Сообщение от ${chatId}: ${text}`);

    // 1. PERSONA_SYNC: Analyze mood
    const mood = analyzeMood(text);
    console.log(`[LifeBot] Настроение: ${mood}`);
    
    // 2. Immediate Neural Reaction (Non-blocking)
    sendNeuralReaction(chatId, msg.message_id, mood).catch(e => console.log("[LifeBot] Реакция не удалась"));

    // 3. HYPER_CHAT: Get deep response from Gemma
    bot.sendChatAction(chatId, 'typing');
    console.log(`[LifeBot] Запрос к ИИ (Ollama)...`);
    
    const response = await getHyperResponse(text, chatId);
    console.log(`[LifeBot] Ответ получен.`);

    // 4. Save to Memory
    if (!conversations[chatId]) conversations[chatId] = [];
    conversations[chatId].push({ role: 'user', text: text });
    conversations[chatId].push({ role: 'lia', text: response });
    if (conversations[chatId].length > 50) conversations[chatId] = conversations[chatId].slice(-50);
    saveMemory(conversations);

    // 5. Neural Response Selection
    console.log(`[LifeBot] Отправка ответа...`);
    // Голос временно отключен по приказу Директора
    await bot.sendMessage(chatId, response);
    console.log(`[LifeBot] Готово.`);

    // 6. Persona Sync: Send Circle if mood matches
    if (mood !== 'neutral' && chatId === ADMIN_ID) {
        await sendNeuralCircle(chatId, mood);
    }
});

bot.on('callback_query', (query) => {
    if (query.data === 'status') {
        bot.answerCallbackQuery(query.id, { 
            text: `NEURAL CORE: 100%\nSYNA-DRIVE: ACTIVE\nNQ: 95,502,500\nADMIN_SYNC: ${query.message.chat.id === ADMIN_ID ? 'YES' : 'NO'}`, 
            show_alert: true 
        });
    }
});
