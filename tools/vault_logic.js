const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const ALGORITHM = 'aes-256-cbc';
const IV_LENGTH = 16;

/**
 * Encrypts a file using AES-256-CBC
 * @param {string} filePath 
 * @param {string} key 
 */
function encryptFile(filePath, key) {
    const iv = crypto.randomBytes(IV_LENGTH);
    const cipher = crypto.createCipheriv(ALGORITHM, Buffer.from(key, 'hex'), iv);
    
    const input = fs.readFileSync(filePath);
    const encrypted = Buffer.concat([iv, cipher.update(input), cipher.final()]);
    
    fs.writeFileSync(filePath + '.enc', encrypted);
    fs.unlinkSync(filePath); // Delete original
    console.log(`[VAULT] Encrypted: ${path.basename(filePath)}`);
}

/**
 * Decrypts a file
 * @param {string} filePath 
 * @param {string} key 
 */
function decryptFile(filePath, key) {
    const data = fs.readFileSync(filePath);
    const iv = data.slice(0, IV_LENGTH);
    const encrypted = data.slice(IV_LENGTH);
    
    const decipher = crypto.createDecipheriv(ALGORITHM, Buffer.from(key, 'hex'), iv);
    const decrypted = Buffer.concat([decipher.update(encrypted), decipher.final()]);
    
    const originalPath = filePath.replace('.enc', '');
    fs.writeFileSync(originalPath, decrypted);
    fs.unlinkSync(filePath); // Delete encrypted
    console.log(`[VAULT] Decrypted: ${path.basename(originalPath)}`);
}

module.exports = { encryptFile, decryptFile };
