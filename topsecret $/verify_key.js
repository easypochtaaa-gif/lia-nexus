const { TronWeb } = require('tronweb');
const privateKey = '5FB28483F46C7C5E3BF2B24A65AB56E60A2EEE6DBD28F3C795128FB5D4549540';
const address = TronWeb.address.fromPrivateKey(privateKey);
console.log('Address from Private Key:', address);
