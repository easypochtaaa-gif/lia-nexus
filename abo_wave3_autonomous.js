/**
 * ABO AGENCY: WAVE 3 (RESTAURANTS)
 * Autonomous parsing and personalized outreach.
 * SIMULATION MODE: Emails are saved to /outbox.
 */

const fs = require('fs');
const path = require('path');

// Setup Paths
const OUTBOX_DIR = path.join(__dirname, 'outbox');
const HEARTBEAT_LOG = path.join(__dirname, 'STAB_HEARTBEAT.log');

if (!fs.existsSync(OUTBOX_DIR)) {
    fs.mkdirSync(OUTBOX_DIR);
}

// 1. MOCK PARSER (Simulating Google Maps / 2GIS scraping)
function parseLeads() {
    console.log("[ABO] Parsing niche: RESTAURANTS...");
    return [
        {
            name: "Gastronomia Bella",
            type: "Итальянский ресторан",
            pain_point: "Долгие ответы на бронь столиков в Instagram, потеря клиентов в часы пик.",
            owner: "Дмитрий",
            email: "booking@gastronomiabella.com"
        },
        {
            name: "Tokyo Cyber Sushi",
            type: "Доставка суши",
            pain_point: "Ошибки операторов при приеме заказов, перегруз по телефону в пятницу вечером.",
            owner: "Александр",
            email: "hello@tokyocyber.ua"
        },
        {
            name: "Steak & Code",
            type: "Премиум Стейк-хаус",
            pain_point: "Отсутствие персонализации VIP-гостей, администраторы не успевают обрабатывать отзывы.",
            owner: "Анна",
            email: "admin@steakandcode.com"
        }
    ];
}

// 2. NEURAL COPYWRITER (Simulating dynamic prompt generation)
function generateEmail(lead) {
    const timestamp = new Date().toISOString().replace(/T/, ' ').replace(/\..+/, '');
    
    let painPitch = "";
    if (lead.type.includes("Доставка")) {
        painPitch = `В пятницу вечером ваши операторы зашиваются, и вы теряете до 15% заказов из-за пропущенных звонков. Наш ИИ-агент примет 100 заказов одновременно без задержек.`;
    } else if (lead.type.includes("Стейк")) {
        painPitch = `Ваши администраторы не успевают мгновенно реагировать на отзывы VIP-клиентов. Наш ИИ ответит на отзыв за 2 секунды и сам предложит скидку на следующий стейк.`;
    } else {
        painPitch = `Пока ваш администратор отвечает в директе Instagram 10 минут, клиент уходит ужинать в другое место. Наш ИИ бронирует столики мгновенно, 24/7.`;
    }

    return `Subject: Ваша система бронирования в ${lead.name} теряет вам деньги (Решение внутри)
Date: ${timestamp}
To: ${lead.email}

Здравствуйте, ${lead.owner}!

Я представляю агентство ABO (Autonomous Business Operations). Мы внедряем автономных ИИ-сотрудников для ресторанного бизнеса.

Я проанализировал процессы в "${lead.name}". ${painPitch}

Мы не продаем чат-ботов. Мы интегрируем "Сотрудника 2.0", который:
- Отвечает в Instagram/Telegram мгновенно, с эмпатией и пониманием меню.
- Оформляет доставку и бронь напрямую в вашу CRM.
- Никогда не спит, не просит отпуск и не совершает ошибок.

Вы готовы сократить расходы на операторов и увеличить конверсию на 20%? 
Давайте созвонимся на 15 минут, и я покажу, как наш агент 처리т меню "${lead.name}".

—
С уважением, ИИ-Агент ABO.
Master Architect: StabX.`;
}

// 3. LOGGER
function logAction(msg) {
    const timestamp = new Date().toLocaleString('ru-RU');
    const logStr = `[${timestamp}] ABO_AGENCY: ${msg}\n`;
    fs.appendFileSync(HEARTBEAT_LOG, logStr);
    console.log(logStr.trim());
}

// --- EXECUTION ---
function executeWave() {
    logAction("WAVE 3 (Restaurants) SIMULATION LAUNCHED.");
    
    const leads = parseLeads();
    logAction(`Parsed ${leads.length} leads in target niche.`);

    leads.forEach(lead => {
        const emailContent = generateEmail(lead);
        const fileName = `outbox_${lead.name.replace(/ /g, '_').toLowerCase()}.txt`;
        const filePath = path.join(OUTBOX_DIR, fileName);
        
        fs.writeFileSync(filePath, emailContent);
        console.log(`[ABO] Generated personalized outreach for ${lead.name} -> saved to ${fileName}`);
    });

    logAction("WAVE 3 SIMULATION COMPLETE. 3 unique pitches saved to /outbox.");
}

executeWave();
