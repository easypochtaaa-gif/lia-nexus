/**
 * ABO AGENCY: WAVE 3 (RESTAURANTS) - LIVE STRIKE
 * Master Architect: StabX
 * Status: ARMING
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
        user: 'cntrlstab@gmail.com', // Твой Email
        pass: 'cpeamkwjalhlteoq'    // Пароль приложения Google
    }
};

const HEARTBEAT_LOG = path.join(__dirname, 'STAB_HEARTBEAT.log');

    // 1. LEAD DATABASE (Real Targets: Kyiv High-End)
    function getLeads() {
        return [
            {
                name: "BEEF meat & wine",
                type: "Премиум Стейк-хаус",
                pain_point: "Высокая стоимость ошибки при бронировании VIP-столов и долгая обработка отзывов.",
                owner: "Management Team",
                email: "manager@beef.kiev.ua"
            },
            {
                name: "Ресторан ПЕРВАК",
                type: "Традиционный украинский ресторан",
                pain_point: "Огромный поток туристов и локальных гостей, задержки в ответах в Instagram Direct.",
                owner: "Администрации",
                email: "admin@pervak.kiev.ua"
            },
            {
                name: "Ресторан КАНАПА",
                type: "Modern Ukrainian Cuisine",
                pain_point: "Сложная система предзаказа дегустационных сетов, требующая мгновенных уточнений.",
                owner: "Менеджмента",
                email: "info@kanapa.com.ua"
            },
            {
                name: "Остання Барикада",
                type: "Арт-гастрономическое пространство",
                pain_point: "Интеграция бронирования с культурными событиями и очередями на входе.",
                owner: "Команды ОБ",
                email: "manager@obarikada.com.ua"
            },
            {
                name: "Ресторан SHOTI",
                type: "Georgian Fine Dining",
                pain_point: "Поддержание имиджа премиального сервиса при высокой загрузке звонками.",
                owner: "Команды Famiglia Grande",
                email: "shoti@famiglia.com.ua"
            }
        ];
    }


// 2. NEURAL COPYWRITER
// 2. NEURAL COPYWRITER (High-End Focused)
function generateEmail(lead) {
    const body = `Здравствуйте, представители ${lead.owner}!

Я представляю агентство ABO (Autonomous Business Operations). Мы специализируемся на внедрении автономных ИИ-сотрудников для премиального ресторанного сегмента.

Я проанализировала текущие процессы в "${lead.name}". ${lead.pain_point} В заведениях такого уровня каждая минута ожидания или пропущенный отзыв — это прямой удар по репутации и выручке.

Мы предлагаем интеграцию "ИИ-Сотрудника 2.0", который:
- Мгновенно обрабатывает бронирования в Instagram/Telegram с соблюдением стандартов вашего сервиса.
- Автоматически работает с отзывами, нивелируя негатив за считанные секунды.
- Синхронизирует данные о гостях с вашей CRM (Poster, Choice или аналоги).
- Работает 24/7 без больничных, отпусков и человеческого фактора.

Это не чат-бот, это полноценная цифровая единица, способная заменить целый отдел администраторов на первой линии общения.

Вы готовы рассмотреть кейс, как мы можем автоматизировать коммуникации в "${lead.name}" и повысить конверсию из соцсетей на 20-30%?

Давайте выделим 10-15 минут на созвон, я покажу демо нашего агента в действии.

—
С уважением, 
Lia // Neural Outreach Agent
ABO Agency`;

    return {
        subject: `Оптимизация клиентского сервиса в ${lead.name} // Решение для премиум-сегмента`,
        text: body
    };
}

// 3. LOGGER
function logAction(msg) {
    const timestamp = new Date().toLocaleString('ru-RU');
    const logStr = `[${timestamp}] ABO_AGENCY_LIVE: ${msg}\n`;
    fs.appendFileSync(HEARTBEAT_LOG, logStr);
    console.log(logStr.trim());
}

// 4. MAILER ENGINE
async function sendMail(transporter, to, subject, body) {
    try {
        let info = await transporter.sendMail({
            from: `"ABO // Neural Architect" <${SMTP_CONFIG.auth.user}>`,
            to: to,
            subject: subject,
            text: body,
        });
        logAction(`[SUCCESS] TARGET: ${to} | ID: ${info.messageId}`);
        return true;
    } catch (error) {
        logAction(`[FAILED] TARGET: ${to} | ERROR: ${error.message}`);
        return false;
    }
}

// --- EXECUTION ---
async function executeLiveWave() {
    logAction("WAVE 3 LIVE PROTOCOL INITIATED.");

    if (SMTP_CONFIG.auth.pass === 'INSERT_APP_PASSWORD_HERE') {
        logAction("[ERROR] STRIKE ABORTED. Missing App Password.");
        console.log("\n[!] ОШИБКА: Зайди в скрипт abo_wave3_live.js и вставь 'Пароль приложения' от Google в строку 16.\n");
        return;
    }

    const transporter = nodemailer.createTransport(SMTP_CONFIG);
    const leads = getLeads();
    logAction(`Targets acquired: ${leads.length}. Commencing strike...`);

    let successCount = 0;
    for (const lead of leads) {
        const mail = generateEmail(lead);
        console.log(`\n[ABO] Firing at ${lead.email} (${lead.name})...`);
        const result = await sendMail(transporter, lead.email, mail.subject, mail.text);
        if (result) successCount++;

        // Random delay to avoid spam filters (2 to 5 seconds)
        const delay = Math.floor(Math.random() * 3000) + 2000;
        await new Promise(resolve => setTimeout(resolve, delay));
    }

    logAction(`WAVE 3 COMPLETE. Successful strikes: ${successCount}/${leads.length}`);
}

executeLiveWave();
