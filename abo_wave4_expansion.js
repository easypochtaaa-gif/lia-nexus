/**
 * ABO AGENCY: WAVE 4 (ALL UKRAINE) - NATIONWIDE EXPANSION
 * Sectors: Legal, Medical, Real Estate
 * Master Architect: StabX
 * Status: INITIALIZING
 */

const fs = require('fs');
const path = require('path');
const nodemailer = require('nodemailer');

// --- CONFIGURATION ---
const SMTP_CONFIG = {
    host: 'smtp.gmail.com',
    port: 465,
    secure: true,
    auth: {
        user: 'cntrlstab@gmail.com', 
        pass: 'cpeamkwjalhlteoq'    
    }
};

const LOG_FILE = path.join(__dirname, 'ABO_EXPANSION_LOG.log');

// --- LEAD DATABASE (NATIONWIDE) ---
const LEADS = [
    // LEGAL SECTOR
    {
        name: "Ильяшев и Партнеры",
        sector: "Legal",
        email: "office@attorneys.ua",
        target: "Партнеров и руководства",
        pitch: "Ваши юристы тратят до 30% времени на первичный скоринг клиентов. Наш ИИ-агент автоматизирует сбор данных и квалификацию лидов 24/7."
    },
    {
        name: "EUCON Law Group",
        sector: "Legal",
        email: "info@euconlaw.com",
        target: "Администрации",
        pitch: "Интеграция ИИ-сотрудника на первую линию общения позволит мгновенно обрабатывать запросы из Европы и Украины одновременно."
    },
    {
        name: "ЮК АРМАДА",
        sector: "Legal",
        email: "info@armada.law",
        target: "Руководства",
        pitch: "Автоматизация записи на консультации через мессенджеры увеличит конверсию входящего трафика на 25% без расширения штата."
    },
    // MEDICAL SECTOR
    {
        name: "Медицинская сеть ДОБРОБУТ",
        sector: "Medical",
        email: "info@dobrobut.com",
        target: "Департамента инноваций",
        pitch: "Снижение нагрузки на контакт-центр за счет автономной записи пациентов на прием через Telegram и Instagram в ночное время."
    },
    {
        name: "Оксфорд Медикал (Oxford Medical)",
        sector: "Medical",
        email: "info@oxford-med.com.ua",
        target: "Маркетинг-директора",
        pitch: "Мгновенное подтверждение записи и ответы на FAQ по услугам клиники силами ИИ-агента с эмпатичным подходом."
    },
    {
        name: "ОН Клиник (ON Clinic)",
        sector: "Medical",
        email: "info@onclinic.ua",
        target: "Администрации",
        pitch: "Автоматизация воронки записи на прием и напоминаний о визите через интеллектуального помощника."
    },
    // REAL ESTATE
    {
        name: "АН Премьер (Одесса)",
        sector: "Real Estate",
        email: "realty@premier.ua",
        target: "Руководства",
        pitch: "В недвижимости выигрывает тот, кто ответил первым. Наш ИИ перехватывает лид в Instagram за 3 секунды, пока он не ушел к конкурентам."
    }
];

// --- NEURAL ENGINE ---
function generatePitch(lead) {
    const body = `Здравствуйте, уважаемые представители ${lead.target} ${lead.name}!

Я представляю агентство ABO (Autonomous Business Operations). Мы внедряем автономных ИИ-сотрудников для оптимизации бизнес-процессов в лидирующих компаниях Украины.

Проанализировав вашу нишу, мы подготовили решение по внедрению "ИИ-Агента 2.0" для ${lead.name}. 

Ключевая ценность:
${lead.pitch}

Наши агенты не просто чат-боты. Это системы на базе LLM последнего поколения (Opus/GPT-o1), которые:
1. Интегрируются с вашими CRM (Bitrix24, amoCRM, Poster).
2. Общаются человеческим языком, понимая контекст и сложные вопросы.
3. Сокращают расходы на колл-центр и администраторов на 40-60%.
4. Обеспечивают мгновенный ответ 24/7 во всех мессенджеры.

Мы готовы предоставить демо-версию агента, настроенную под специфику ${lead.name}, чтобы вы увидели результат до начала внедрения.

Предлагаю провести короткую презентацию (15 минут) на этой неделе. Когда вам было бы удобно?

—
С уважением, 
Lia // Neural Outreach System
ABO Agency`;

    return {
        subject: `Цифровая трансформация и оптимизация ${lead.sector} процессов в ${lead.name}`,
        text: body
    };
}

// --- CORE FUNCTIONS ---
function log(msg) {
    const timestamp = new Date().toLocaleString('ru-RU');
    const entry = `[${timestamp}] ABO_EXPANSION: ${msg}\n`;
    fs.appendFileSync(LOG_FILE, entry);
    console.log(entry.trim());
}

async function sendMail(transporter, lead) {
    const mail = generatePitch(lead);
    try {
        let info = await transporter.sendMail({
            from: `"ABO // Autonomous Systems" <${SMTP_CONFIG.auth.user}>`,
            to: lead.email,
            subject: mail.subject,
            text: mail.text
        });
        log(`[SUCCESS] TARGET: ${lead.email} | ID: ${info.messageId}`);
        return true;
    } catch (err) {
        log(`[FAILED] TARGET: ${lead.email} | ERROR: ${err.message}`);
        return false;
    }
}

async function main() {
    log("WAVE 4: NATIONWIDE EXPANSION INITIATED.");
    const transporter = nodemailer.createTransport(SMTP_CONFIG);
    
    let sent = 0;
    for (const lead of LEADS) {
        log(`Firing at ${lead.name} (${lead.sector})...`);
        const result = await sendMail(transporter, lead);
        if (result) sent++;
        
        // Anti-spam delay
        const delay = Math.floor(Math.random() * 5000) + 3000;
        await new Promise(r => setTimeout(r, delay));
    }
    
    log(`WAVE 4 COMPLETE. Total successful strikes: ${sent}/${LEADS.length}`);
}

main();
