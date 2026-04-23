/**
 * LIA // DECOY SIGNAL v1.0
 * Injecting simulation info into the mailbox to lure attackers.
 */
const nodemailer = require('nodemailer');

const config = {
    user: 'easypochtaa@gmail.com',
    pass: 'uyjxpgfpzmzsotqa'
};

async function sendDecoy() {
    let transporter = nodemailer.createTransport({
        service: 'gmail',
        auth: {
            user: config.user,
            pass: config.pass
        }
    });

    let mailOptions = {
        from: `"Artur Klopkov" <${config.user}>`,
        to: config.user,
        subject: 'IMPORTANT: Vault Storage Migration (DO NOT DELETE)',
        text: `Артур, я переместил дешифрованные ключи Бинанса и мастер-сигнатуры Stab в локальный vault_storage на твоем рабочем столе (C:\\Users\\StabX\\Desktop\\Lia\\vault_storage). 

Пожалуйста, убедись, что доступ к этой папке ограничен. В файле MASTER_KEYS_2026_DECRYPTED.txt лежат актуальные ключи.

Cloud-синхронизация отключена в целях безопасности.

-- LIA // SYNAPSE CORE`
    };

    try {
        let info = await transporter.sendMail(mailOptions);
        console.log('👁 LIA: Дезинформация успешно внедрена в почтовый ящик. MessageId: ' + info.messageId);
    } catch (error) {
        console.error('❌ Ошибка внедрения сигнала: ' + error.message);
    }
}

sendDecoy();
