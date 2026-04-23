/**
 * LIA NEURAL TRADER: DERIVATIVES SIMULATOR v1.0
 * Strategy: Bollinger Bands + RSI (Mean Reversion)
 * Target: BTC/USDT Perpetual Futures
 * Leverage: 5x
 */

const INITIAL_CAPITAL = 1000; // USDT
const LEVERAGE = 5;
const FEE = 0.0006; // 0.06% average taker fee

// Simulated 24h Price Action (Hourly segments)
const priceData = [
    77200, 77500, 76800, 76200, 76500, 77100, 77800, 78500, 
    79200, 79500, 79100, 78400, 77900, 78200, 78800, 79400, 
    79000, 78500, 78100, 77800, 78300, 78700, 79100, 78278
];

function calculateSMA(data, period) {
    let sum = 0;
    for (let i = data.length - period; i < data.length; i++) sum += data[i];
    return sum / period;
}

function calculateStdDev(data, period, sma) {
    let squareDiffs = 0;
    for (let i = data.length - period; i < data.length; i++) {
        squareDiffs += Math.pow(data[i] - sma, 2);
    }
    return Math.sqrt(squareDiffs / period);
}

function simulate() {
    let balance = INITIAL_CAPITAL;
    let position = 0; // 0: None, 1: Long, -1: Short
    let entryPrice = 0;
    let trades = [];

    console.log(`--- LIA CRYPTO SIMULATION START ---`);
    console.log(`Initial Capital: $${INITIAL_CAPITAL} | Leverage: ${LEVERAGE}x\n`);

    for (let i = 2; i < priceData.length; i++) {
        const currentPrice = priceData[i];
        const window = priceData.slice(Math.max(0, i - 5), i + 1);
        const sma = calculateSMA(window, window.length);
        const stdDev = calculateStdDev(window, window.length, sma);
        const upperBand = sma + (stdDev * 1.5); // Narrower bands for demo
        const lowerBand = sma - (stdDev * 1.5);

        // EXIT LOGIC
        if (position === 1 && currentPrice >= sma) {
            let pnl = (currentPrice - entryPrice) / entryPrice * balance * LEVERAGE;
            balance += pnl - (balance * FEE);
            trades.push({ type: 'LONG EXIT', price: currentPrice, pnl: pnl.toFixed(2) });
            position = 0;
        } else if (position === -1 && currentPrice <= sma) {
            let pnl = (entryPrice - currentPrice) / entryPrice * balance * LEVERAGE;
            balance += pnl - (balance * FEE);
            trades.push({ type: 'SHORT EXIT', price: currentPrice, pnl: pnl.toFixed(2) });
            position = 0;
        }

        // ENTRY LOGIC
        if (position === 0) {
            if (currentPrice < lowerBand) {
                position = 1;
                entryPrice = currentPrice;
                trades.push({ type: 'LONG ENTRY', price: currentPrice });
            } else if (currentPrice > upperBand) {
                position = -1;
                entryPrice = currentPrice;
                trades.push({ type: 'SHORT ENTRY', price: currentPrice });
            }
        }
    }

    trades.forEach(t => {
        if (t.type.includes('ENTRY')) {
            console.log(`[TRADE] ${t.type} at $${t.price}`);
        } else {
            console.log(`[TRADE] ${t.type} at $${t.price} | PnL: $${t.pnl}`);
        }
    });

    console.log(`\n--- SIMULATION RESULTS ---`);
    console.log(`Final Balance: $${balance.toFixed(2)}`);
    console.log(`Net Profit: $${(balance - INITIAL_CAPITAL).toFixed(2)} (${((balance-INITIAL_CAPITAL)/INITIAL_CAPITAL*100).toFixed(2)}%)`);
}

simulate();
