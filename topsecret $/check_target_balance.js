const { TronWeb } = require('tronweb');
const address = 'TJBWLD61pUgcui4g6Tj1pf7Kgs3WX62o1H';
const tronWeb = new TronWeb({ fullHost: 'https://api.trongrid.io' });

async function checkBalance() {
    try {
        const balance = await tronWeb.trx.getBalance(address);
        console.log(`TRX Balance of ${address}: ${balance / 1e6} TRX`);
        
        const contract = await tronWeb.contract().at('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t');
        // Need to set a dummy address for the call
        tronWeb.setAddress('TNDU9as9ndYVpC5yVTMU19r1VTMU19r1V1'); 
        const usdtBalance = await contract.balanceOf(address).call();
        console.log(`USDT Balance of ${address}: ${usdtBalance / 1e6} USDT`);
    } catch (e) {
        console.error('Error checking balance:', e);
    }
}
checkBalance();
