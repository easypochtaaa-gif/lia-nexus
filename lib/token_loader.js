const fs = require('fs');
const path = require('path');

// Ensure we load .env if not already loaded
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const localTokenPath = path.join(__dirname, '..', 'config', 'token.json');

function getToken() {
  // Priority 1: Environment Variables
  const token = process.env.TELEGRAM_BOT_TOKEN || process.env.BOT_TOKEN;
  if (token) {
    return token;
  }

  // Priority 2: Local File
  try {
    if (fs.existsSync(localTokenPath)) {
      const raw = fs.readFileSync(localTokenPath, 'utf8');
      return JSON.parse(raw).tg_bot_token;
    }
  } catch (e) {
    console.error('⚠️ [TOKEN_LOADER] Failed to read token from local file:', e.message);
  }

  return null;
}

module.exports = { getToken };
