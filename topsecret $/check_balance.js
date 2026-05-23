const { TronWeb } = require('tronweb');
const address = 'TC9KHP5GbApVm2YAtzEd6Ack9DvbMcJLJX';
const tronWeb = new TronWeb({ fullHost: 'https://api.trongrid.io' });

async function checkBalance() {
    try {
        const balance = await tronWeb.trx.getBalance(address);
        console.log(`TRX Balance: ${balance / 1e6} TRX`);
        
        const contract = await tronWeb.contract().at('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t');
        const usdtBalance = await contract.balanceOf(address).call();
        console.log(`USDT Balance: ${usdtBalance / 1e6} USDT`);
    } catch (e) {
        console.error('Error checking balance:', e);
    }
}
checkBalance();
