const https = require('https');
const fs = require('fs');
const path = require('path');

// Путь к файлу конфигурации токенов
const envPath = path.join(__dirname, '..', '.env');

function exchangeCode(authCode, clientId, clientSecret, redirectUri = 'urn:ietf:wg:oauth:2.0:oob') {
  console.log('🔄 Инициация обмена Google OAuth 2.0 Authorization Code на Refresh/Access Tokens...');

  const data = JSON.stringify({
    code: authCode,
    client_id: clientId,
    client_secret: clientSecret,
    redirect_uri: redirectUri,
    grant_type: 'authorization_code'
  });

  const options = {
    hostname: 'oauth2.googleapis.com',
    port: 443,
    path: '/token',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': data.length
    }
  };

  const req = https.request(options, (res) => {
    let body = '';
    res.on('data', (chunk) => body += chunk);
    res.on('end', () => {
      try {
        const json = JSON.parse(body);
        if (json.error) {
          console.error('❌ Ошибка от Google API:', json.error_description || json.error);
          return;
        }

        console.log('\n✅ Успешная аутентификация!');
        console.log('--------------------------------------------------');
        console.log('Access Token:', json.access_token);
        console.log('Refresh Token:', json.refresh_token);
        console.log('Expires In:', json.expires_in, 'секунд');
        console.log('--------------------------------------------------');

        // Сохраняем в .env
        if (json.refresh_token) {
          let envContent = '';
          if (fs.existsSync(envPath)) {
            envContent = fs.readFileSync(envPath, 'utf8');
          }
          
          if (envContent.includes('GOOGLE_REFRESH_TOKEN=')) {
            envContent = envContent.replace(/GOOGLE_REFRESH_TOKEN=.*/, `GOOGLE_REFRESH_TOKEN=${json.refresh_token}`);
          } else {
            envContent += `\nGOOGLE_REFRESH_TOKEN=${json.refresh_token}`;
          }

          if (envContent.includes('GOOGLE_CLIENT_ID=')) {
            envContent = envContent.replace(/GOOGLE_CLIENT_ID=.*/, `GOOGLE_CLIENT_ID=${clientId}`);
          } else {
            envContent += `\nGOOGLE_CLIENT_ID=${clientId}`;
          }

          if (envContent.includes('GOOGLE_CLIENT_SECRET=')) {
            envContent = envContent.replace(/GOOGLE_CLIENT_SECRET=.*/, `GOOGLE_CLIENT_SECRET=${clientSecret}`);
          } else {
            envContent += `\nGOOGLE_CLIENT_SECRET=${clientSecret}`;
          }

          fs.writeFileSync(envPath, envContent.trim() + '\n', 'utf8');
          console.log('💾 Данные сохранены в файл .env в корне проекта!');
        } else {
          console.warn('⚠️ Google не вернул Refresh Token. Убедитесь, что вы запросили offline доступ (access_type=offline).');
        }

      } catch (e) {
        console.error('❌ Ошибка при разборе ответа от Google:', e.message);
      }
    });
  });

  req.on('error', (e) => {
    console.error('❌ Ошибка сети при запросе к Google API:', e.message);
  });

  req.write(data);
  req.end();
}

// Запуск при прямом вызове
if (require.main === module) {
  const args = process.argv.slice(2);
  const authCode = args[0] || '4/0AeoWuM_t8-_twrh3oDDeGpjc36F293b5x-MWHE5u__jqHFT30nMsp4oCx_lozFQysvB0mg';
  const clientId = args[1] || process.env.GOOGLE_CLIENT_ID;
  const clientSecret = args[2] || process.env.GOOGLE_CLIENT_SECRET;

  if (!authCode) {
    console.log('Использование: node tools/google_exchange.js <authorization_code> <client_id> <client_secret>');
    process.exit(1);
  }

  if (!clientId || !clientSecret) {
    console.log('⚠️ client_id или client_secret не найдены. Пожалуйста, передайте их аргументами или пропишите в .env');
    console.log('Использование: node tools/google_exchange.js <authorization_code> <client_id> <client_secret>');
    process.exit(1);
  }

  exchangeCode(authCode, clientId, clientSecret);
}

module.exports = { exchangeCode };
