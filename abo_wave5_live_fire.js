const fs = require('fs');
const path = require('path');
const nodemailer = require('nodemailer');

const SMTP_CONFIG = {
    host: 'smtp.gmail.com',
    port: 465,
    secure: true,
    auth: {
        user: 'cntrlstab@gmail.com',
        pass: 'cpeamkwjalhlteoq'
    }
};

const targets = [
    { name: 'Monobank', email: 'oleg.gorokhovsky@monobank.ua', c_level: 'Oleg', pain: 'Scalability of human support during market volatility.' },
    { name: 'SoftServe', email: 'yaroslav.lyubinets@softserve.ua', c_level: 'Yaroslav', pain: 'Optimizing internal resource allocation via AI agents.' },
    { name: 'Grammarly', email: 'brad.hoover@grammarly.com', c_level: 'Brad', pain: 'Deep-level automation of non-core administrative overhead.' }
];

async function fire() {
    const transporter = nodemailer.createTransport(SMTP_CONFIG);
    console.log("--- ABO_AGENCY: LIVE FIRE INITIATED ---");

    for (const target of targets) {
        const body = `
Уважаемый ${target.c_level},

Я представляю агентство ABO (Autonomous Business Operations). Мы идентифицировали зону роста в ${target.name}, которая может дать вам +30% к операционной эффективности.

Ваша текущая проблема: ${target.pain}

Мы предлагаем внедрение автономных ИИ-агентов класса "Nexus". Мы уже работаем в юридическом и медицинском секторах Украины.

Готовы выделить 10 минут на закрытую демонстрацию?

--
Master Architect: StabX.
ABO Agency.
        `.trim();

        try {
            await transporter.sendMail({
                from: `"HERMES // Stab Imperium" <${process.env.SMTP_USER}>`,
                to: target.email,
                subject: `Оптимизация архитектуры ${target.name} (Конфиденциально)`,
                text: body
            });
            console.log(`[SUCCESS] Strike on ${target.name} confirmed. Email sent.`);
        } catch (err) {
            console.error(`[FAILED] Strike on ${target.name}: ${err.message}`);
        }
    }
    console.log("--- MISSION COMPLETE ---");
}

fire();
