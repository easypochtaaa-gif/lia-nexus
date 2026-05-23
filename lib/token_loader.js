const fs = require('fs');
const path = require('path');

const localTokenPath = path.join(__dirname, '..', 'config', 'token.json');
const brainTokenPath = path.resolve('C:/Users/StabX/.gemini/antigravity/brain/3febc255-e8de-4a47-9cee-c7e9c5563068/config/token.json');

function getToken() {
  // Priority 1: Environment Variable (Recommended for Render/Heroku)
  if (process.env.TELEGRAM_BOT_TOKEN) {
    return process.env.TELEGRAM_BOT_TOKEN;
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

  // Priority 3: Brain File
  try {
    if (fs.existsSync(brainTokenPath)) {
      const raw = fs.readFileSync(brainTokenPath, 'utf8');
      return JSON.parse(raw).tg_bot_token;
    }
  } catch (e) {
    console.error('⚠️ [TOKEN_LOADER] Failed to read token from brain file:', e.message);
  }

  return null;
}

module.exports = { getToken };
