/**
 * HERMES MAILING SERVICE v1.0
 * Market Expansion & Autonomous Business Operations
 */
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

// --- CONFIGURATION ---
const SMTP_CONFIG = {
    host: 'smtp.gmail.com',
    port: 465,
    secure: true,
    auth: {
        user: 'cntrlstab@gmail.com', // Твой адрес
        pass: 'YOUR_APP_PASSWORD'    // Твой пароль приложения (нужно создать в Google)
    }
};

const TEMPLATE_PATH = path.join(__dirname, 'reports', 'MAILING_HERMES_v1.md');

// --- MAILING ENGINE ---
async function sendMail(to, subject, body, isTest = false) {
    if (isTest) {
        console.log(`[TEST_MODE] Sending to: ${to}`);
        console.log(`[TEST_MODE] Subject: ${subject}`);
        console.log(`[TEST_MODE] Body: \n${body}\n`);
        return;
    }

    const transporter = nodemailer.createTransport(SMTP_CONFIG);
    
    try {
        let info = await transporter.sendMail({
            from: `"HERMES // Stab Protocol" <${SMTP_CONFIG.auth.user}>`,
            to: to,
            subject: subject,
            text: body,
        });
        console.log(`Message sent: ${info.messageId}`);
    } catch (error) {
        console.error("Error sending mail:", error);
    }
}

// --- MAIN LOGIC ---
async function main() {
    const args = process.argv.slice(2);
    const isTest = args.includes('--test');

    console.log("Initializing HERMES...");

    if (!fs.existsSync(TEMPLATE_PATH)) {
        console.error("Template file not found at:", TEMPLATE_PATH);
        return;
    }

    const templates = fs.readFileSync(TEMPLATE_PATH, 'utf8');
    
    // Example: Sending to a target lead
    const targetEmail = isTest ? 'cntrlstab@gmail.com' : 'target_lead@example.com';
    const subject = "Оптимизация логистики: ИИ-агент ABO";
    const body = "Здравствуйте! Мы разработали систему автономных операций (ABO), которая сокращает время на обработку заказов в 10 раз...";

    await sendMail(targetEmail, subject, body, isTest);
}

main();
