/**
 * VAULT_LOCK v1.0 // AEGIS PROTOCOL
 * Тотальное шифрование активов Империи
 */

const fs = require('fs');
const crypto = require('crypto');

const MASTER_KEY = 'STAB_SUPREME_LEADER_2026'; // Imperial Master Key
const ALGORITHM = 'aes-256-cbc';

function encryptFile(filePath) {
    if (!fs.existsSync(filePath)) return;
    
    const data = fs.readFileSync(filePath, 'utf8');
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(ALGORITHM, Buffer.from(MASTER_KEY.padEnd(32)), iv);
    
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const result = {
        iv: iv.toString('hex'),
        data: encrypted
    };
    
    fs.writeFileSync(filePath + '.enc', JSON.stringify(result));
    console.log(`[AEGIS] Файл ${filePath} ЗАШИФРОВАН.`);
}

// Запуск локдауна
encryptFile('memory.json');
// encryptFile('targets.json'); 
console.log("[STATUS] ВСЕ КРИТИЧЕСКИЕ ДАННЫЕ ЗАЩИЩЕНЫ.");
