const { TronWeb } = require('tronweb');
const address = 'TC9KHP5GbApVm2YAtzEd6Ack9DvbMcJLJX';

async function checkNile() {
    const tronWeb = new TronWeb({ fullHost: 'https://api.nileex.io' });
    try {
        const balance = await tronWeb.trx.getBalance(address);
        console.log(`NILE TRX Balance: ${balance / 1e6} TRX`);
        
        const contract = await tronWeb.contract().at('TXLAQReffhSEvCdwmqaqnZ76AtS6837vXJ'); // Nile USDT
        tronWeb.setAddress(address);
        const usdtBalance = await contract.balanceOf(address).call();
        console.log(`NILE USDT Balance: ${usdtBalance / 1e6} USDT`);
    } catch (e) {
        console.log('Not on Nile or error:', e.message);
    }
}
checkNile();
