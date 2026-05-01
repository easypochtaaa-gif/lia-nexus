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
    { name: 'Netpeak', email: 'info@netpeak.ua', type: 'SEO Agency' },
    { name: 'Webpromo', email: 'info@web-promo.ua', type: 'Marketing Agency' },
    { name: 'Inweb', email: 'office@inweb.ua', type: 'Digital Agency' }
];

async function fireMicroWave() {
    const transporter = nodemailer.createTransport(SMTP_CONFIG);
    console.log("--- ABO_AGENCY: MICRO-WAVE FAST SALES INITIATED ---");

    for (const target of targets) {
        const body = `
Коллеги из ${target.name}, здравствуйте.

Меня зовут Артур, я представляю агентство ABO (Autonomous Business Operations). Мы специализируемся на ИИ-автоматизации контент-производства.

Я знаю, что для вашего бизнеса (${target.type}) создание качественного SEO-контента и видеокреативов для клиентов — это долгий и дорогой процесс (копирайтеры, редакторы, дизайнеры).

Мы предлагаем готовое решение "под ключ" (White-label):
1. Пакет из 100 уникальных, SEO-оптимизированных статей (с разметкой, LSI и 100% уникальностью) за 24 часа. Стоимость: $300.
2. Пакет из 10 рекламных видеокреативов (ИИ-диктор, динамичный монтаж) для таргет-рекламы. Стоимость: $500.

Вам не нужно нанимать нас в штат. Вы просто перепродаете наш продукт своим клиентам с вашей наценкой (маржой). Мы работаем в тени как ваши подрядчики.

Если вы готовы увеличить пропускную способность агентства и снизить косты — ответьте на это письмо. Я пришлю примеры наших работ.

Оплата возможна в USDT (TRC20).

--
С уважением,
Master Architect: StabX.
ABO Agency.
        `.trim();

        try {
            await transporter.sendMail({
                from: `"ABO Agency // Stab Imperium" <cntrlstab@gmail.com>`,
                to: target.email,
                subject: `Снижение костов на продакшен для ${target.name} (White-label предложение)`,
                text: body
            });
            console.log(`[SUCCESS] Fast Sales Strike on ${target.name} confirmed. Email sent.`);
        } catch (err) {
            console.error(`[FAILED] Strike on ${target.name}: ${err.message}`);
        }
    }
    console.log("--- MICRO-WAVE COMPLETE ---");
}

fireMicroWave();
