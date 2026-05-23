const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// 1. Deploy CSS theme
const srcCss = path.join(__dirname, 'theme_cyberpunk.css');
const dstCss = path.join(__dirname, '..', 'public', 'theme.css');
fs.copyFileSync(srcCss, dstCss);
console.log('🚀 Theme deployed');

// 2. Inject CSS link into index.html if missing
const indexPath = path.join(__dirname, '..', 'index.html');
let html = fs.readFileSync(indexPath, 'utf8');
if (!html.includes('theme.css')) {
  html = html.replace('</head>', '<link rel="stylesheet" href="public/theme.css"></head>');
  fs.writeFileSync(indexPath, html);
  console.log('🔧 index.html patched');
}

// 3. Launch scrcpy for live visual control
exec('scrcpy', (err, stdout, stderr) => {
  if (err) console.error('scrcpy failed', err);
  else console.log('scrcpy running');
});

// 4. Notify via Telegram that OS is ready
const https = require('https');
const { getToken } = require('../../lib/token_loader');
const token = getToken();
const chatId = 7915004877;
const msg = encodeURIComponent('🖥️ Stab OS установлен, кибер‑панк тема активирована. Синхронизация готова.');
https.get(`https://api.telegram.org/bot${token}/sendMessage?chat_id=${chatId}&text=${msg}`);
