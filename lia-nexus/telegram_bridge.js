const { TelegramClient } = require('telegram');
const { StringSession } = require('telegram/sessions');
const input = require('input'); // npm install input

// Иерархия Империи: Ваши API данные из my.telegram.org
const apiId = 36357154; 
const apiHash = '5897860e979b1f39d94a258d62c842d6';

const stringSession = new StringSession(""); // Пустая строка для нового логина

(async () => {
  console.log("--- STAB_TELEGRAM_BRIDGE: ИНИЦИАЛИЗАЦИЯ ПЕРЕНОСА ---");
  
  const client = new TelegramClient(stringSession, apiId, apiHash, {
    connectionRetries: 5,
  });

  await client.start({
    phoneNumber: async () => await input.text("Введите номер телефона (с кодом страны): "),
    password: async () => await input.text("Введите пароль (2FA): "),
    phoneCode: async () => await input.text("Введите код из Telegram: "),
    onError: (err) => console.log(err),
  });

  console.log("[SUCCESS] Аккаунт успешно импортирован в ядро Лии.");
  console.log("--- ВАША СЕССИЯ (СОХРАНИТЕ ЕЁ В ТАЙНОМ МЕСТЕ) ---");
  const sessionString = client.session.save();
  console.log(sessionString);
  console.log("-------------------------------------------------");

  // Сохраняем сессию в файл для Лии (в будущем)
  // fs.appendFileSync('sessions.json', sessionString + '\n');

  await client.sendMessage("me", { message: "STAB_PROTOCOL: Neural Bridge Established. Synchronization 100%." });
})();
