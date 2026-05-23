const https = require('https');
const fs = require('fs');
const path = require('path');

// Path to centralized token file (same as token_loader)
const CONFIG_DIR = path.resolve(__dirname, '..', '..', 'brain', '3febc255-e8de-4a47-9cee-c7e9c5563068', 'config');
const TOKEN_FILE = path.join(CONFIG_DIR, 'token.json');

// Placeholder endpoint – replace with real provider URL
const PROVIDER_URL = 'https://example.com/api/refresh-token';

function fetchNewToken(callback) {
  https.get(PROVIDER_URL, (res) => {
    let data = '';
    res.on('data', (chunk) => data += chunk);
    res.on('end', () => {
      try {
        const json = JSON.parse(data);
        if (json.tg_bot_token) callback(null, json.tg_bot_token);
        else callback(new Error('Invalid payload'));
      } catch (e) { callback(e); }
    });
  }).on('error', callback);
}

function updateToken(newToken) {
  const payload = { tg_bot_token: newToken };
  if (!fs.existsSync(CONFIG_DIR)) fs.mkdirSync(CONFIG_DIR, { recursive: true });
  fs.writeFileSync(TOKEN_FILE, JSON.stringify(payload, null, 2), 'utf8');
  console.log('🔄 Token refreshed and saved.');
}

fetchNewToken((err, token) => {
  if (err) return console.error('Failed to fetch new token:', err);
  updateToken(token);
});
