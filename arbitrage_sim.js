const axios = require('axios');
const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(__dirname, 'arbitrage_results.log');
const INITIAL_CAPITAL = 10000;
let currentBalance = INITIAL_CAPITAL;
const FEE = 0.001; // 0.1% per trade

const TARGET_SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'ETHBTC',
    'BNBUSDT', 'BNBBTC', 'BNBETH',
    'SOLUSDT', 'SOLBTC', 'SOLETH',
    'XRPUSDT', 'XRPBTC'
];

async function logResult(msg) {
    const timestamp = new Date().toLocaleString('ru-RU');
    const fullMsg = `[${timestamp}] ${msg}\n`;
    fs.appendFileSync(LOG_FILE, fullMsg);
    console.log(fullMsg.trim());
}

async function getPrices() {
    try {
        const response = await axios.get('https://api.binance.com/api/v3/ticker/bookTicker', { timeout: 5000 });
        const data = response.data;
        
        const prices = {};
        data.forEach(item => {
            if (TARGET_SYMBOLS.includes(item.symbol)) {
                prices[item.symbol] = {
                    bid: parseFloat(item.bidPrice),
                    ask: parseFloat(item.askPrice)
                };
            }
        });
        return prices;
    } catch (error) {
        return null;
    }
}

function calculatePath(balance, p1, p2, p3) {
    // Standard: USDT -> ASSET1 (Buy) -> ASSET2 (Buy/Sell) -> USDT (Sell)
    if (!p1 || !p2 || !p3) return 0;
    
    // Path: USDT -> p1.symbol (Buy) -> p2.symbol (Buy/Sell) -> p3.symbol (Sell)
    // For ETHBTC: Buying BTC with ETH is selling ETH for BTC. 
    // Wait, the logic needs to be precise.
    
    // USDT -> p1 (Buy Asset1)
    let asset1 = (balance / p1.ask) * (1 - FEE);
    // Asset1 -> p2 (Sell Asset1 for Asset2)
    let asset2 = (asset1 * p2.bid) * (1 - FEE);
    // Asset2 -> p3 (Sell Asset2 for USDT)
    let result = (asset2 * p3.bid) * (1 - FEE);
    
    return result;
}

async function runCycle() {
    const p = await getPrices();
    if (!p) return;

    const paths = [
        { name: 'ETH-BTC', result: calculatePath(currentBalance, p.ETHUSDT, p.ETHBTC, p.BTCUSDT) },
        { name: 'BNB-BTC', result: calculatePath(currentBalance, p.BNBUSDT, p.BNBBTC, p.BTCUSDT) },
        { name: 'BNB-ETH', result: calculatePath(currentBalance, p.BNBUSDT, p.BNBETH, p.ETHUSDT) },
        { name: 'SOL-BTC', result: calculatePath(currentBalance, p.SOLUSDT, p.SOLBTC, p.BTCUSDT) },
        { name: 'SOL-ETH', result: calculatePath(currentBalance, p.SOLUSDT, p.SOLETH, p.ETHUSDT) }
    ];

    paths.forEach(path => {
        const profit = path.result - currentBalance;
        if (profit > 0.01) {
            currentBalance = path.result;
            logResult(`[💰 PROFIT] [${path.name}] +${profit.toFixed(4)} | New Balance: ${currentBalance.toFixed(2)}`);
        }
    });
}

logResult(`👁 LIA: Расширение протокола арбитража (v1.2). Пул активов: BTC, ETH, BNB, SOL. Баланс: ${currentBalance}`);
setInterval(runCycle, 2000); // 2s interval for faster detection
