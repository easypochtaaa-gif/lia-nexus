require('dotenv').config();
const OpenAI = require('openai');
const nodemailer = require('nodemailer');

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

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
    { name: 'Sotheby\'s Digital', email: 'digitalart@sothebys.com', contact: 'Curator', bio: 'Looking for the next generation of high-end cybernetic art.' },
    { name: 'SuperRare Labs', email: 'editorial@superrare.com', contact: 'Curation Team', bio: 'Focusing on exclusive, single-edition digital masterpieces.' },
    { name: 'Art Blocks', email: 'info@artblocks.io', contact: 'Integrations', bio: 'Generative and procedural art enthusiasts with a focus on blockchain.' }
];

async function generateMessage(target) {
    const prompt = `Write a short, elite, and mysterious business proposal for ${target.name}. 
    We are STAB IMPERIUM. We sell high-end digital NFT art (Observer Effect collection, Cybernetic Armor, Neural Keys).
    The tone should be 'Luxury Tech House' - professional but edgy and exclusive.
    Target context: ${target.bio}.
    Refer to ${target.contact}.
    Language: Russian (if target name sounds Slavic) or English (for international).
    Limit to 3 short paragraphs. End with: 'Master Architect: StabX. Stab Imperium.'`;

    const response = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.7,
    });

    return response.choices[0].message.content;
}

async function runStrike() {
    console.log("--- STAB_PROTOCOL: NEURAL STRIKE INITIATED ---");
    const transporter = nodemailer.createTransport(SMTP_CONFIG);

    for (const target of targets) {
        console.log(`[ANALYZING] Generating custom neural offer for ${target.name}...`);
        const body = await generateMessage(target);

        const mailOptions = {
            from: `"STAB IMPERIUM // GALLERY" <cntrlstab@gmail.com>`,
            to: target.email,
            subject: `Exclusive Access: The Stab Artifacts // ${target.name}`,
            text: body
        };

        try {
            await transporter.sendMail(mailOptions);
            console.log(`[SUCCESS] Neural strike on ${target.name} confirmed.`);
        } catch (err) {
            console.error(`[FAILED] Strike on ${target.name}: ${err.message}`);
        }
    }
    console.log("--- MISSION COMPLETE: DOMINANCE SECURED ---");
}

runStrike();
