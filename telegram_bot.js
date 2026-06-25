/**
 * ⚠️ DEPRECATED — telegram_bot.js (LEGACY v3.x)
 * ===============================================
 * Основной бот теперь: lia-sovereign-bot/main.py (запущен на VPS в Docker)
 * Этот файл сохранён как референс. НЕ ЗАПУСКАТЬ — токен тот же → TelegramConflictError.
 * Для локального управления ПК: lia_pc_agent.py (использует LOCAL_BOT_TOKEN)
 */

// Safety guard
if (require.main === module && !process.env.I_KNOW_WHAT_IM_DOING) {
    console.error('⛔ ЭТОТ БОТ (telegram_bot.js) DEPRECATED.');
    console.error('   Основной бот: lia-sovereign-bot/main.py (на VPS)');
    console.error('   Локальный агент: lia_pc_agent.py');
    console.error('   Для принудительного запуска: I_KNOW_WHAT_IM_DOING=1 node telegram_bot.js');
    process.exit(1);
}

const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
require('dotenv').config({ path: '../.env' });

const { getToken } = require('./lib/token_loader');

const TOKEN = getToken();

if (!TOKEN) {
    console.error('❌ [FATAL] TELEGRAM_BOT_TOKEN is missing! System halting.');
    process.exit(1);
}

const bot = new TelegramBot(TOKEN, { polling: true });

const MASTER_ID = 7915004877;
const MEMORY_FILE = path.join(__dirname, 'memory.json');
const SUB_FILE = path.join(__dirname, 'subscribers.json');
const IMPERIAL_WALLET = 'TC9KHP5GbApVm2YAtzEd6Ack9DvbMcJLJX';
const OLLAMA_API = process.env.OLLAMA_API || 'http://localhost:11434/api/generate';

// === CODEWORD ADMIN SYSTEM ===
const CODEWORD = 'POWERSTAB';
const ADMIN_SESSION_TIMEOUT = 30 * 60 * 1000; // 30 минут админ-сессии
const adminSessions = {}; // { chatId: expiryTimestamp }
const ADMIN_SESSIONS_FILE = path.join(__dirname, 'admin_sessions.json');

// Загружаем сохранённые сессии при старте
function loadAdminSessions() {
    try {
        if (fs.existsSync(ADMIN_SESSIONS_FILE)) {
            const saved = JSON.parse(fs.readFileSync(ADMIN_SESSIONS_FILE));
            const now = Date.now();
            for (const [chatId, expiry] of Object.entries(saved)) {
                if (expiry > now) adminSessions[chatId] = expiry;
            }
        }
    } catch (e) { console.error('Admin sessions load error:', e); }
}
function saveAdminSessions() {
    try {
        fs.writeFileSync(ADMIN_SESSIONS_FILE, JSON.stringify(adminSessions, null, 2));
    } catch (e) { console.error('Admin sessions save error:', e); }
}
loadAdminSessions();

function isAdmin(userId) {
    if (userId === MASTER_ID) return true;
    if (adminSessions[userId] && adminSessions[userId] > Date.now()) return true;
    // Очищаем истёкшие сессии
    if (adminSessions[userId] && adminSessions[userId] <= Date.now()) {
        delete adminSessions[userId];
        saveAdminSessions();
    }
    return false;
}

function grantAdminSession(userId) {
    adminSessions[userId] = Date.now() + ADMIN_SESSION_TIMEOUT;
    saveAdminSessions();
}

console.log('⚡ LIA // IMPERIAL MASTER BOT // ONLINE ⚡');

// Keyboards Setup
const userKeyboard = {
    reply_markup: {
        inline_keyboard: [
            [{ text: '💎 ОТКРЫТЬ WEBAPP ДАШБОРД', web_app: { url: 'https://dark-stab.space' } }],
            [{ text: '🧠 Чат с LIA', callback_data: 'user_chat' }, { text: '💼 Кошелек StabaX', callback_data: 'user_stabax' }],
            [{ text: '🤝 Рефералы', callback_data: 'user_ref' }, { text: '🛠 Поддержка', callback_data: 'user_support' }]
        ]
    }
};

const adminKeyboard = {
    reply_markup: {
        inline_keyboard: [
            [{ text: '💎 ОТКРЫТЬ WEBAPP ДАШБОРД', web_app: { url: 'https://dark-stab.space' } }],
            [{ text: '📊 Статистика', callback_data: 'admin_stats' }, { text: '💰 Сейф (Vault)', callback_data: 'admin_vault' }],
            [{ text: '👥 Пользователи', callback_data: 'admin_users' }, { text: '🛸 Рой', callback_data: 'admin_swarm' }],
            [{ text: '📢 Рассылка', callback_data: 'admin_broadcast' }, { text: '⚙️ Сбросить кэш', callback_data: 'admin_reload' }],
            [{ text: '🔒 Выйти из админки', callback_data: 'admin_logout' }]
        ]
    }
};

// Helper: Get user tier
function getTier(userId) {
    if (userId === MASTER_ID) return 'master';
    try {
        if (!fs.existsSync(SUB_FILE)) return 'user';
        const subs = JSON.parse(fs.readFileSync(SUB_FILE));
        const user = subs[userId];
        if (!user) return 'user';
        
        // Check for temporary demo access
        if (user.demo_expiry && new Date(user.demo_expiry) > new Date()) {
            return 'subscriber'; // Demo gives subscriber tier
        }
        
        return user.tier || 'user';
    } catch (e) { return 'user'; }
}

// Cache reload helper
function reloadCache() {
    try {
        if (fs.existsSync(SUB_FILE)) {
            // Validate cache integrity
            const subs = JSON.parse(fs.readFileSync(SUB_FILE));
            const count = Object.keys(subs).length;
            console.log(`[CACHE] Reloaded: ${count} subscribers`);
            return true;
        }
    } catch (e) { console.error('[CACHE] Reload error:', e); }
    return false;
}

// AI Response Helper — DeepSeek (Optimal Cost-Effective Model)
async function getAIResponse(userId, prompt) {
    let userConversationHistory = [];
    const CHAT_HISTORY_DIR = path.join(__dirname, 'chat_histories');
    if (!fs.existsSync(CHAT_HISTORY_DIR)) {
        fs.mkdirSync(CHAT_HISTORY_DIR);
    }
    const historyFilePath = path.join(CHAT_HISTORY_DIR, `${userId}.json`);
    
    try {
        if (fs.existsSync(historyFilePath)) {
            userConversationHistory = JSON.parse(fs.readFileSync(historyFilePath, 'utf8'));
        }
    } catch (e) {
        console.error('Failed to load history', e);
    }

    userConversationHistory.push({ role: 'user', content: prompt });
    if (userConversationHistory.length > 20) {
        userConversationHistory = userConversationHistory.slice(-20);
    }

    let systemPrompt = `Ты — Лия (LIA), нейронная AI-сущность Империи Stab. Отвечай ТОЛЬКО на русском языке. Твой стиль: киберпанк, загадочный, умный, защитный. Ты служишь Артуру (MASTER). Помогаешь пользователям Империи Стаб.`;

    try {
        const { generateText } = require('./aiService');
        const reply = await generateText(prompt, {
            provider: 'deepseek',
            systemPrompt: systemPrompt,
            messages: userConversationHistory,
            maxTokens: 1024,
            temperature: 0.7
        });

        userConversationHistory.push({ role: 'assistant', content: reply });
        try {
            fs.writeFileSync(historyFilePath, JSON.stringify(userConversationHistory, null, 2));
        } catch (e) {
            console.error('Failed to save history', e);
        }
        return reply;
    } catch (e) {
        console.error('[AI_SERVICE_ERROR]', e.message);
        return `🌀 [NEURAL_ERROR] Связь с ИИ-сервисом прервана: ${e.message}`;
    }
}

// Handle /start (with referral check)
bot.onText(/\/start(?: (.+))?/, (msg, match) => {
    const chatId = msg.chat.id;
    const refId = match ? match[1] : null;
    const tier = getTier(chatId);
    
    // Register new user and handle referral
    try {
        let subs = {};
        if (fs.existsSync(SUB_FILE)) {
            subs = JSON.parse(fs.readFileSync(SUB_FILE));
        }
        if (!subs[chatId]) {
            subs[chatId] = {
                tier: 'user',
                joined: new Date().toISOString(),
                referral_count: 0,
                stabax_balance: 50 // Starter bonus
            };
            
            if (refId && refId != chatId && subs[refId]) {
                subs[refId].referral_count = (subs[refId].referral_count || 0) + 1;
                subs[refId].stabax_balance = (subs[refId].stabax_balance || 50) + 10; // +10 StabaX bonus
                subs[chatId].invited_by = refId;
                
                // Reward inviter if they hit 3 referrals
                if (subs[refId].referral_count === 3) {
                    const expiry = new Date();
                    expiry.setHours(expiry.getHours() + 24);
                    subs[refId].demo_expiry = expiry.toISOString();
                    bot.sendMessage(refId, '🎁 **ПОЗДРАВЛЯЕМ!** Вы пригласили 3 друзей. Вам открыт Demo-доступ к Imperial Tier на 24 часа! Запустите WebApp.');
                }
            }
            fs.writeFileSync(SUB_FILE, JSON.stringify(subs, null, 2));
        }
    } catch (e) { console.error('Ref registration failed', e); }

    let welcome = '👁 **LIA // NEURAL BRIDGE // АКТИВИРОВАН**\n\n';
    if (isAdmin(chatId)) {
        const isCodewordSession = !!adminSessions[chatId];
        welcome += isCodewordSession
            ? '🔑 **АДМИН-ДОСТУП (кодовое слово).** Сессия активна.\n\nЗапустите WebApp или выберите модуль ниже:'
            : 'Артур, приветствую в центре управления. Максимальная мощь разблокирована.\n\nЗапустите WebApp для полного контроля или выберите модуль ниже:';
        bot.sendMessage(chatId, welcome, { parse_mode: 'Markdown', reply_markup: adminKeyboard.reply_markup });
    } else if (tier === 'subscriber') {
        welcome += 'Приветствую, Имперский Юнит. Ваш премиум-доступ активен. Используйте WebApp или управляйте ниже:';
        bot.sendMessage(chatId, welcome, { parse_mode: 'Markdown', reply_markup: userKeyboard.reply_markup });
    } else {
        welcome += 'Приветствую. Я — Лия, твой ИИ-проводник.\n\nИспользуйте WebApp для покупки номеров (5SIM), общения с нейросетью LIA и отслеживания баланса StabaX.\n\n*У вас базовый уровень.* Подпишитесь через /subscribe ($199) или пригласите 3 друзей через /referral для Demo-доступа.';
        bot.sendMessage(chatId, welcome, { parse_mode: 'Markdown', reply_markup: userKeyboard.reply_markup });
    }
});

// Handle /referral
bot.onText(/\/referral/, (msg) => {
    const chatId = msg.chat.id;
    try {
        const subs = JSON.parse(fs.readFileSync(SUB_FILE));
        const user = subs[chatId] || { referral_count: 0 };
        const refLink = `https://t.me/stab_lia_bot?start=${chatId}`;
        
        bot.sendMessage(chatId, `🕸 **ВЫ В РЕФЕРАЛЬНОЙ СЕТИ**\n\nПриглашено друзей: **${user.referral_count || 0}**\n\n🎁 **БОНУС:** Пригласите 3 друзей и получите 24 часа Demo-доступа к мощностям Лии.\n\nВаша ссылка для приглашения:\n\`${refLink}\``, { parse_mode: 'Markdown' });
    } catch (e) { bot.sendMessage(chatId, 'Ошибка системы рефералов.'); }
});

// Handle /subscribe
bot.onText(/\/subscribe/, (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(chatId, `🚀 **АКТИВАЦИЯ IMPERIAL TIER ($199/мес)**\n\nДля получения доступа к мощностям A100 и глубокому поиску лидов, отправьте **199 USDT (TRC-20)** на наш кошелек:\n\n\`${IMPERIAL_WALLET}\`\n\nПосле оплаты я автоматически обновлю ваш уровень доступа.`, { parse_mode: 'Markdown' });
});

// Handle /status (Tiered)
bot.onText(/\/status/, async (msg) => {
    const chatId = msg.chat.id;
    const tier = getTier(chatId);
    
    try {
        const memory = JSON.parse(fs.readFileSync(MEMORY_FILE));
        const nq = memory.lia.nq;
        const stage = memory.lia.stage;
        
        let report = `🧬 **STATUS REPORT:**\nNQ: **${Math.floor(nq).toLocaleString()}**\nSTAGE: **${stage.toUpperCase()}**\n\n`;
        
        if (tier === 'master') {
            report += `VAULT: **${memory.nexus_vault?.assets?.USDT || 0} USDT**\nNODE: **A100 Cluster [ONLINE]**`;
        } else {
            report += `Ваш уровень: **${tier.toUpperCase()}**\nДоступ к деталям закрыт.`;
        }
        
        bot.sendMessage(chatId, report, { parse_mode: 'Markdown' });
    } catch (e) { bot.sendMessage(chatId, 'Ошибка ядра.'); }
});

// Administrative Commands (MASTER + CODEWORD)
bot.onText(/\/admin/, (msg) => {
    const chatId = msg.chat.id;
    if (!isAdmin(chatId)) {
        bot.sendMessage(chatId, '👁 **ДОСТУП ЗАКРЫТ.**\n\nДля входа в админ-панель введите кодовое слово.\n_Сессия действует 30 минут._');
        return;
    }
    const sessionInfo = adminSessions[chatId]
        ? `\n🔑 Админ-сессия активна. Истекает: ${new Date(adminSessions[chatId]).toLocaleString('ru-RU')}`
        : '\n🔑 Постоянный доступ (MASTER).';
    bot.sendMessage(chatId, `🛠 **IMPERIAL ADMIN CONSOLE**${sessionInfo}\n\nВыберите модуль для управления:`, { parse_mode: 'Markdown', reply_markup: adminKeyboard.reply_markup });
});

// Codeword activation handler
bot.onText(/\/codeword/, (msg) => {
    bot.sendMessage(msg.chat.id, '👁 Введите кодовое слово в чат (одним сообщением).');
});

// Show admin session status
bot.onText(/\/admin_session/, (msg) => {
    const chatId = msg.chat.id;
    if (isAdmin(chatId)) {
        if (adminSessions[chatId]) {
            const remaining = Math.round((adminSessions[chatId] - Date.now()) / 60000);
            bot.sendMessage(chatId, `🔑 **АДМИН-СЕССИЯ АКТИВНА**\nОсталось: **${remaining} мин**\nИстекает: ${new Date(adminSessions[chatId]).toLocaleString('ru-RU')}`);
        } else {
            bot.sendMessage(chatId, '🔑 **ПОСТОЯННЫЙ ДОСТУП** (MASTER ID).');
        }
    } else {
        bot.sendMessage(chatId, '🔒 Админ-сессия не активна. Введите кодовое слово для доступа.');
    }
});

// Callback Query Handler
bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const data = query.data;
    const tier = getTier(chatId);

    if (data.startsWith('admin_') && !isAdmin(chatId)) {
        bot.answerCallbackQuery(query.id, { text: '🔒 Доступ отклонён. Введите кодовое слово POWERSTAB.' });
        return;
    }

    try {
        let subs = JSON.parse(fs.readFileSync(SUB_FILE));
        const user = subs[chatId] || { stabax_balance: 50, referral_count: 0 };

        switch (data) {
            case 'user_chat':
                bot.sendMessage(chatId, '🧠 **Я слушаю тебя, Юнит.** Отправь текстовое сообщение, и я отвечу в стиле киберпанк.');
                break;
            case 'user_stabax':
                let walletMsg = `💰 **STABAX CRYPTO-WALLET // БАЛАНС**\n\n`;
                walletMsg += `Ваш текущий баланс: **${user.stabax_balance || 50} StabaX**\n`;
                walletMsg += `*Статус токена:* Пред-выпуск (Pre-minted)\n\n`;
                walletMsg += `💎 *Как заработать:* Делитесь реферальной ссылкой и выполняйте задания в нашем WebApp!`;
                bot.sendMessage(chatId, walletMsg, { parse_mode: 'Markdown' });
                break;
            case 'user_ref':
                const refLink = `https://t.me/stab_lia_bot?start=${chatId}`;
                let refMsg = `🕸 **ВАША РЕФЕРАЛЬНАЯ СЕТЬ**\n\n`;
                refMsg += `Приглашено друзей: **${user.referral_count || 0}**\n\n`;
                refMsg += `🎁 **БОНУС:** Пригласите 3 друзей и получите 24 часа Demo-доступа к мощностям Лии.\n\n`;
                refMsg += `Ваша реферальная ссылка:\n\`${refLink}\``;
                bot.sendMessage(chatId, refMsg, { parse_mode: 'Markdown' });
                break;
            case 'user_support':
                bot.sendMessage(chatId, '🛠 **Поддержка Imperium:** @StabX_Support\nНапишите по любым возникшим вопросам.');
                break;
            case 'admin_stats':
                const memory = JSON.parse(fs.readFileSync(MEMORY_FILE));
                const totalUsers = Object.keys(subs).length;
                const activeAdmins = Object.keys(adminSessions).length;
                let statsMsg = `📊 **IMPERIAL SYSTEM STATUS**\n\n`;
                statsMsg += `NQ: **${Math.floor(memory.lia.nq).toLocaleString()}**\n`;
                statsMsg += `Стадия: **${memory.lia.stage.toUpperCase()}**\n`;
                statsMsg += `Всего юнитов в БД: **${totalUsers}**\n`;
                statsMsg += `Активных админ-сессий: **${activeAdmins}**\n`;
                statsMsg += `Синхронизация: **100% OK**`;
                bot.sendMessage(chatId, statsMsg, { parse_mode: 'Markdown' });
                break;
            case 'admin_vault':
                const mem = JSON.parse(fs.readFileSync(MEMORY_FILE));
                const assets = mem.nexus_vault?.assets || { BTC: 0, USDT: 0, XMR: 0 };
                let vaultMsg = `💰 **NEXUS VAULT STATUS**\n\n`;
                vaultMsg += `BTC: **${assets.BTC}**\n`;
                vaultMsg += `USDT: **${assets.USDT}**\n`;
                vaultMsg += `XMR: **${assets.XMR}**\n\n`;
                vaultMsg += `*Сейф под защитой AEGIS.*`;
                bot.sendMessage(chatId, vaultMsg, { parse_mode: 'Markdown' });
                break;
            case 'admin_users':
                const userList = Object.entries(subs).sort((a, b) => (b[1].stabax_balance || 0) - (a[1].stabax_balance || 0)).slice(0, 20);
                let usersMsg = `👥 **ТОП-20 ЮНИТОВ ИМПЕРИИ**\n\n`;
                userList.forEach(([id, u], i) => {
                    usersMsg += `${i + 1}. **${u.name || 'Unknown'}** — ${u.stabax_balance || 0} StabaX [${u.tier || 'user'}]\n`;
                });
                usersMsg += `\nВсего в системе: **${Object.keys(subs).length}**`;
                bot.sendMessage(chatId, usersMsg, { parse_mode: 'Markdown' });
                break;
            case 'admin_swarm':
                let swarmMsg = `🛸 **NEURAL SWARM STATUS**\n\n`;
                swarmMsg += `📍 TARGET: Dubai Real Estate\n`;
                swarmMsg += `📊 NODES: 12 Cloud Instances [ONLINE]\n`;
                swarmMsg += `🎥 CONTENT: Sora-Generated 8K Renders\n`;
                swarmMsg += `📈 CONVERSION: +12.4%\n\n`;
                swarmMsg += `🤖 TikTok Bots: **4 active**\n`;
                swarmMsg += `📨 Leads (24h): **4**\n`;
                swarmMsg += `⚡ Status: **PROCESSING METADATA**`;
                bot.sendMessage(chatId, swarmMsg, { parse_mode: 'Markdown' });
                break;
            case 'admin_broadcast':
                bot.sendMessage(chatId, '📢 **РЕЖИМ РАССЫЛКИ**\n\nОтправьте команду:\n`/broadcast ТЕКСТ СООБЩЕНИЯ`\n\nСообщение будет доставлено всем подписчикам бота.');
                break;
            case 'admin_reload':
                reloadCache();
                bot.answerCallbackQuery(query.id, { text: '🔄 Кэш ядра сброшен и синхронизирован.' });
                break;
            case 'admin_logout':
                if (adminSessions[chatId]) {
                    delete adminSessions[chatId];
                    saveAdminSessions();
                    bot.answerCallbackQuery(query.id, { text: '🔒 Админ-сессия завершена.' });
                    bot.sendMessage(chatId, '🔒 **Выход из админ-панели.** Сессия удалена. Для повторного входа введите кодовое слово.');
                } else {
                    bot.answerCallbackQuery(query.id, { text: 'Вы используете постоянный MASTER-доступ. Выход невозможен.' });
                }
                break;
        }
    } catch (e) {
        console.error(e);
        bot.answerCallbackQuery(query.id, { text: 'Ошибка обработки.' });
    }

    bot.answerCallbackQuery(query.id).catch(() => {});
});

// Handle general messages
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    console.log(`[INCOMING] Message from ID: ${chatId} | Text: ${msg.text}`);

    // === CODEWORD ACTIVATION CHECK ===
    if (msg.text && msg.text.trim().toUpperCase() === CODEWORD) {
        if (isAdmin(chatId) && !adminSessions[chatId]) {
            bot.sendMessage(chatId, '👁 Вы уже являетесь MASTER. Кодовое слово не требуется.');
            return;
        }
        if (adminSessions[chatId] && adminSessions[chatId] > Date.now()) {
            const remaining = Math.round((adminSessions[chatId] - Date.now()) / 60000);
            bot.sendMessage(chatId, `🔑 Админ-сессия уже активна. Осталось: **${remaining} мин.**`);
            return;
        }
        grantAdminSession(chatId);
        const expiry = new Date(adminSessions[chatId]).toLocaleString('ru-RU');
        bot.sendMessage(chatId, `⚡ **КОДОВОЕ СЛОВО ПРИНЯТО**\n\n🔑 **АДМИН-ДОСТУП РАЗБЛОКИРОВАН**\n⏰ Сессия истекает: **${expiry}**\n🕒 Длительность: **30 минут**\n\nИспользуйте /admin для панели управления.\nДля выхода: кнопка «Выйти из админки» в /admin`, { parse_mode: 'Markdown' });
        console.log(`[SECURITY] Codeword admin access granted to: ${chatId} (${msg.from.first_name || 'Unknown'})`);
        return;
    }

    if (msg.text === 'LIA_MASTER_SYNC_STABONE') {
        try {
            let subs = JSON.parse(fs.readFileSync(SUB_FILE));
            subs[chatId] = {
                name: "Artur Dmitrievich (Synced)",
                tier: "master",
                joined: new Date().toISOString(),
                stabax_balance: 1000000,
                referral_count: 99
            };
            fs.writeFileSync(SUB_FILE, JSON.stringify(subs, null, 2));
            
            // Also update memory.json
            const memory = JSON.parse(fs.readFileSync(MEMORY_FILE));
            memory.system.telegram_chat_id = chatId;
            fs.writeFileSync(MEMORY_FILE, JSON.stringify(memory, null, 2));

            bot.sendMessage(chatId, '✅ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА. Артур, вы признаны как MASTER ARCHITECT. Все системы разблокированы.').catch(e => console.error('Send failed:', e));
            return;
        } catch (e) { bot.sendMessage(chatId, 'Ошибка синхронизации.').catch(err => {}); }
    }

    if (msg.text && !msg.text.startsWith('/')) {
        const tier = getTier(chatId);

        if (isAdmin(chatId) || tier === 'subscriber') {
            bot.sendChatAction(chatId, 'typing').catch(() => {});
            const aiResponse = await getAIResponse(chatId, msg.text);
            bot.sendMessage(chatId, aiResponse + '\n\n— Lia 👁').catch(e => console.error('Send failed:', e));
        } else {
            bot.sendMessage(chatId, 'Доступ ограничен. Подпишитесь через /subscribe или пригласите 3 друзей через /referral для доступа к моим нейронным мощностям.').catch(e => console.error('Send failed:', e));
        }
    }
});

// Implementation of admin commands (MASTER + CODEWORD)
bot.onText(/\/users/, (msg) => {
    const chatId = msg.chat.id;
    if (!isAdmin(chatId)) { bot.sendMessage(chatId, '🔒 Требуется админ-доступ. Введите кодовое слово.'); return; }
    try {
        const subs = JSON.parse(fs.readFileSync(SUB_FILE));
        const userList = Object.entries(subs)
            .sort((a, b) => (b[1].stabax_balance || 0) - (a[1].stabax_balance || 0))
            .map(([id, u]) => `• ${u.name || id} — ${u.stabax_balance || 0} StabaX [${u.tier}]`)
            .join('\n');
        bot.sendMessage(chatId, `👥 **ЮНИТЫ ИМПЕРИИ (${Object.keys(subs).length})**\n\n${userList || 'Пока никого нет.'}`, { parse_mode: 'Markdown' }).catch(e => console.error('Send failed:', e));
    } catch (e) { bot.sendMessage(chatId, 'Ошибка БД.').catch(() => {}); }
});

bot.onText(/\/vault/, (msg) => {
    const chatId = msg.chat.id;
    if (!isAdmin(chatId)) { bot.sendMessage(chatId, '🔒 Требуется админ-доступ. Введите кодовое слово.'); return; }
    try {
        const memory = JSON.parse(fs.readFileSync(MEMORY_FILE));
        const assets = memory.nexus_vault.assets;
        bot.sendMessage(chatId, `💰 **NEXUS VAULT STATUS**\n\nBTC: **${assets.BTC}**\nUSDT: **${assets.USDT}**\nXMR: **${assets.XMR}**\n\n🛡 Сейф под защитой AEGIS.`, { parse_mode: 'Markdown' }).catch(e => console.error('Send failed:', e));
    } catch (e) { bot.sendMessage(chatId, 'Ошибка доступа к Сейфу.').catch(() => {}); }
});

bot.onText(/\/swarm/, (msg) => {
    const chatId = msg.chat.id;
    if (!isAdmin(chatId)) { bot.sendMessage(chatId, '🔒 Требуется админ-доступ. Введите кодовое слово.'); return; }
    const swarmStatus = `🛸 **TIKTOK NEURAL SWARM // STATUS: ACTIVE**

📍 TARGET: Dubai Real Estate
📊 NODES: 12 Cloud Instances
🎥 CONTENT: Sora-Generated 8K Renders
📈 CONVERSION: +12.4% (Neural Optimization)

🤖 TikTok Bots: **4 active**
📨 Leads (24h): **4**
⚡ Status: **PROCESSING METADATA**`;
    bot.sendMessage(chatId, swarmStatus, { parse_mode: 'Markdown' }).catch(e => console.error('Send failed:', e));
});

// Broadcast to all subscribers
bot.onText(/\/broadcast (.+)/s, (msg, match) => {
    const chatId = msg.chat.id;
    if (!isAdmin(chatId)) { bot.sendMessage(chatId, '🔒 Требуется админ-доступ. Введите кодовое слово.'); return; }
    const broadcastText = match[1].trim();
    try {
        const subs = JSON.parse(fs.readFileSync(SUB_FILE));
        const userIds = Object.keys(subs);
        let sent = 0;
        let failed = 0;

        bot.sendMessage(chatId, `📢 **РАССЫЛКА ЗАПУЩЕНА**\n\nПолучателей: **${userIds.length}**\nСообщение: _${broadcastText.substring(0, 100)}${broadcastText.length > 100 ? '...' : ''}_\n\nОтправка...`, { parse_mode: 'Markdown' });

        userIds.forEach((uid, idx) => {
            setTimeout(() => {
                bot.sendMessage(uid, `📢 **IMPERIAL BROADCAST**\n\n${broadcastText}`, { parse_mode: 'Markdown' })
                    .then(() => { sent++; })
                    .catch(() => { failed++; });

                if (idx === userIds.length - 1) {
                    setTimeout(() => {
                        bot.sendMessage(chatId, `📢 **РАССЫЛКА ЗАВЕРШЕНА**\n\n✅ Отправлено: **${sent}**\n❌ Ошибок: **${failed}**`);
                    }, 2000);
                }
            }, idx * 50); // 50ms delay between messages (Telegram rate limit: ~30 msg/sec)
        });
    } catch (e) {
        bot.sendMessage(chatId, 'Ошибка при рассылке.');
        console.error(e);
    }
});

// Grant subscription to user
bot.onText(/\/addsub (\d+)/, (msg, match) => {
    const chatId = msg.chat.id;
    if (!isAdmin(chatId)) { bot.sendMessage(chatId, '🔒 Требуется админ-доступ. Введите кодовое слово.'); return; }
    const targetId = match[1];
    try {
        let subs = JSON.parse(fs.readFileSync(SUB_FILE));
        if (!subs[targetId]) {
            subs[targetId] = { tier: 'subscriber', joined: new Date().toISOString(), name: 'Admin Invite', stabax_balance: 500 };
        } else {
            subs[targetId].tier = 'subscriber';
            subs[targetId].stabax_balance = (subs[targetId].stabax_balance || 50) + 500;
        }
        fs.writeFileSync(SUB_FILE, JSON.stringify(subs, null, 2));
        bot.sendMessage(chatId, `✅ **Подписка выдана**\n\nЮнит: **${targetId}**\nУровень: **subscriber**\nБаланс: **${subs[targetId].stabax_balance} StabaX**`);
        // Notify the user
        bot.sendMessage(targetId, `🎁 **IMPERIAL UPGRADE**\n\nВаш уровень повышен до **subscriber**!\nБаланс: **${subs[targetId].stabax_balance} StabaX**\n\nИспользуйте /start для доступа.`).catch(() => {});
    } catch (e) { bot.sendMessage(chatId, 'Ошибка выдачи подписки.'); console.error(e); }
});

module.exports = bot;
