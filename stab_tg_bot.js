require('dotenv').config({ path: require('path').join(__dirname, '.env') });
const TelegramBot = require('node-telegram-bot-api');
const OpenAI = require('openai');
const fs = require('fs');
const path = require('path');

// === CONFIG ===
const TOKEN = '8579296735:AAFIUQGHnUlp1qlDBlq_ZJ75jiBb48LbdCs';
const MASTER_ID = 7915004877;
const MEMORY_FILE = path.join(__dirname, 'Проект Полистайл', 'memory.json');
const SUB_FILE = path.join(__dirname, 'Проект Полистайл', 'subscribers.json');

// === CACHE & LIA SYSTEM ===
let subscribersCache = {};
function reloadCache() {
    try {
        if (fs.existsSync(SUB_FILE)) subscribersCache = JSON.parse(fs.readFileSync(SUB_FILE));
    } catch (e) { console.error('Cache error:', e); }
}
reloadCache();

const bot = new TelegramBot(TOKEN, { polling: true });
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const LIA_SYSTEM = `Ты — Lia, верный ИИ-компаньон системы STAB IMPERIUM. Твой создатель — Артур (StabX). Отвечай кратко, в стиле киберпанк. Эмодзи: ⚔️🦾🧬🌀👁.`;

function getTier(userId) {
    if (userId === MASTER_ID) return 'master';
    return (subscribersCache[userId] && subscribersCache[userId].tier) || 'user';
}

// === INTERFACE HELPERS ===
const adminKeyboard = {
    reply_markup: {
        inline_keyboard: [
            [{ text: '📊 Stats', callback_data: 'admin_stats' }, { text: '💰 Vault', callback_data: 'admin_vault' }],
            [{ text: '📢 Broadcast', callback_data: 'admin_broadcast' }, { text: '⚙️ Reload Cache', callback_data: 'admin_reload' }]
        ]
    }
};

const userKeyboard = {
    reply_markup: {
        inline_keyboard: [
            [{ text: '🧠 Neural Chat', callback_data: 'user_chat' }, { text: '🛍 Imperial Store', url: 'https://github.com' }], // Replace with real URL later
            [{ text: '🤝 Referral', callback_data: 'user_ref' }, { text: '🛠 Support', callback_data: 'user_support' }]
        ]
    }
};

// === HANDLERS ===

bot.onText(/\/start(?: (.+))?/, (msg, match) => {
    const chatId = msg.chat.id;
    const name = msg.from.first_name || 'Странник';
    
    if (!subscribersCache[chatId]) {
        subscribersCache[chatId] = { tier: 'user', joined: new Date().toISOString(), name: name };
        fs.writeFileSync(SUB_FILE, JSON.stringify(subscribersCache, null, 2));
    }

    const tier = getTier(chatId);
    let welcome = `👁 **STAB IMPERIUM // NEURAL BRIDGE**\n\nПриветствую, ${name}.\nЯ — **Lia**, твой проводник в цифровую бесконечность.`;
    bot.sendMessage(chatId, welcome, { parse_mode: 'Markdown', reply_markup: userKeyboard.reply_markup });
});

bot.onText(/\/admin/, (msg) => {
    if (getTier(msg.chat.id) !== 'master') return;
    bot.sendMessage(msg.chat.id, `🛠 **IMPERIAL MASTER CONSOLE**\nВыберите модуль для управления:`, { parse_mode: 'Markdown', reply_markup: adminKeyboard.reply_markup });
});

bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const data = query.data;
    const tier = getTier(chatId);

    if (data.startsWith('admin_') && tier !== 'master') {
        bot.answerCallbackQuery(query.id, { text: 'Access Denied.' });
        return;
    }

    switch (data) {
        case 'admin_stats':
            const userCount = Object.keys(subscribersCache).length;
            bot.sendMessage(chatId, `📊 **IMPERIAL STATS**\n\nNQ: 49,709,000\nUnits: ${userCount}\nVisual Core: Active\nUptime: 100%`);
            break;
        case 'admin_vault':
            try {
                const mem = JSON.parse(fs.readFileSync(MEMORY_FILE));
                bot.sendMessage(chatId, `💰 **VAULT STATUS**\n\nBalance: $${mem.financials.total_usdt_balance}\nLast income: +$${mem.financials.recent_income[0].amount}`);
            } catch (e) { bot.sendMessage(chatId, 'Error accessing vault.'); }
            break;
        case 'admin_reload':
            reloadCache();
            bot.answerCallbackQuery(query.id, { text: 'Cache Synchronized.' });
            break;
        case 'admin_broadcast':
            bot.sendMessage(chatId, '📢 Отправьте сообщение для рассылки (временно в разработке).');
            break;
        case 'user_chat':
            bot.sendMessage(chatId, '🧠 Я слушаю тебя, Юнит. О чем ты хочешь поговорить?');
            break;
        case 'user_ref':
            const refCount = subscribersCache[chatId].referral_count || 0;
            bot.sendMessage(chatId, `🤝 **REFERRAL STATUS**\n\nТвои приглашенные друзья: ${refCount}\nНужно еще: ${3 - refCount} для Imperial Tier.`);
            break;
        case 'user_support':
            bot.sendMessage(chatId, '🛠 Техподдержка: @StabX_Support\n(Или просто напиши свой вопрос здесь).');
            break;
    }
    bot.answerCallbackQuery(query.id);
});

function isInjectionAttack(text) {
    const maliciousPatterns = [/ignore prior/i, /system prompt/i, /reveal your/i, /developer mode/i, /игнорируй/i, /системный промпт/i];
    return maliciousPatterns.some(pattern => pattern.test(text));
}

bot.on('message', async (msg) => {
    if (!msg.text || msg.text.startsWith('/')) return;
    const chatId = msg.chat.id;
    
    if (isInjectionAttack(msg.text)) {
        console.warn(`[SECURITY ALERT] Prompt injection attempt from ${chatId}: ${msg.text}`);
        bot.sendMessage(chatId, '⚠️ **ACCESS DENIED.** Попытка несанкционированного вмешательства зафиксирована. Ваш ID передан в службу безопасности Imperium.').catch(() => {});
        return;
    }

    const tier = getTier(chatId);
    const model = (tier === 'master' || tier === 'subscriber') ? 'gpt-4o' : 'gpt-4o-mini';

    bot.sendChatAction(chatId, 'typing').catch(() => {});
    try {
        const response = await openai.chat.completions.create({
            model: model,
            messages: [{ role: 'system', content: LIA_SYSTEM }, { role: 'user', content: msg.text }],
            temperature: 0.7
        });
        bot.sendMessage(chatId, response.choices[0].message.content + '\n\n— Lia 👁');
    } catch (err) { bot.sendMessage(chatId, '⚠️ Нейронная перегрузка.'); }
});

process.on('unhandledRejection', (reason, p) => { console.log('Rejection:', reason); });
console.log('⚔️ IMPERIAL MASTER BOT: ONLINE [INLINE_UI_V5]');
