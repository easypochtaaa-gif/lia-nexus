require('dotenv').config();
const TronWeb = require('tronweb');

const privateKey = process.env.TRON_PRIVATE_KEY;
const senderAddress = process.env.TRON_SENDER_ADDRESS;
const targetAddress = 'TJBWLD61pUgcui4g6Tj1pf7Kgs3WX62o1H';
const usdtContractAddress = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t';
const amount = 10; // 10 USDT

const tronWeb = new TronWeb({
    fullHost: 'https://api.trongrid.io',
    privateKey: privateKey
});

async function sendUSDT() {
    console.log(`[SYSTEM]: Инициализация перевода 10 USDT...`);
    console.log(`[FROM]: ${senderAddress}`);
    console.log(`[TO]: ${targetAddress}`);

    try {
        const contract = await tronWeb.contract().at(usdtContractAddress);
        
        // USDT has 6 decimals
        const decimals = 6;
        const amountWithDecimals = amount * Math.pow(10, decimals);

        console.log(`[ACTION]: Вызов метода transfer...`);
        const result = await contract.transfer(
            targetAddress,
            amountWithDecimals
        ).send();

        console.log(`[SUCCESS]: Транзакция отправлена!`);
        console.log(`[HASH]: ${result}`);
        process.exit(0);
    } catch (error) {
        console.error(`[ERROR]: Ошибка при отправке USDT:`, error);
        process.exit(1);
    }
}

sendUSDT();
