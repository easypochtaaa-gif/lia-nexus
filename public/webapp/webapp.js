const tg = window.Telegram.WebApp;

// Initialize
tg.expand();
tg.ready();

// Set user info
const user = tg.initDataUnsafe?.user;
const userId = user?.id || null;
if (user) {
    document.getElementById('user-name').textContent = user.first_name || "Странник";
}

// Load profile from server
async function loadProfile() {
    if (!userId) return;
    try {
        const res = await fetch(`/api/user-profile?user_id=${userId}`);
        const data = await res.json();
        if (data.found) {
            document.getElementById('requests-left').textContent = (data.tier === 'free' ? 10 : data.tier === 'lite' ? 50 : 200);
            document.getElementById('aegis-score').textContent = data.xp || 0;
            document.getElementById('streak').textContent = data.stab_coins || 0;
            document.getElementById('user-tier').textContent = (data.tier || 'FREE').toUpperCase();
            if (data.wallet) {
                document.getElementById('wallet-status').textContent = '✅ Привязан';
                document.getElementById('wallet-addr').textContent = data.wallet.slice(0, 12) + '...';
            }
        }
    } catch(e) { console.error('Profile load error:', e); }
}
loadProfile();

// Button actions
document.querySelectorAll('.menu-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const action = btn.getAttribute('data-action');

        // Haptic feedback
        tg.HapticFeedback.impactOccurred('medium');

        if (action === 'chat' || action === 'aegis' || action === 'premium') {
            const command = action === 'chat' ? 'chat_start' : (action === 'aegis' ? 'aegis_start' : 'premium_info');
            try {
                tg.sendData(JSON.stringify({ action: command }));
                tg.close();
            } catch (e) {
                tg.showAlert(`Команда ${command} отправлена. Вернитесь в чат с ботом.`);
                tg.close();
            }
        } else if (action === 'wallet') {
            showWalletDialog();
        } else if (action === 'referral') {
            if (userId) {
                const refLink = `https://t.me/stab_lia_bot?start=${userId}`;
                tg.showPopup({
                    title: '🤝 Реферальная ссылка',
                    message: `Приглашай друзей и получай +500 StabaX за каждого!\n\nТвоя ссылка:\n${refLink}`,
                    buttons: [
                        {type: 'default', text: '📋 Копировать', id: 'copy_ref'},
                        {type: 'cancel', text: 'Закрыть'}
                    ]
                }, (btnId) => {
                    if (btnId === 'copy_ref') {
                        tg.sendData(JSON.stringify({ action: 'copy_ref', link: refLink }));
                        tg.showAlert('Ссылка скопирована!');
                    }
                });
            }
        } else {
            tg.showAlert(`Модуль ${action} в разработке.`);
        }
    });
});

// ═══════════ WALLET DIALOG ═══════════
function showWalletDialog() {
    // Show popup with options
    tg.showPopup({
        title: '💎 ПРИВЯЗАТЬ КОШЕЛЁК',
        message: 'Web3 кошелёк для получения StabaX.\n\n'
            + '⚠️ MetaMask/Phantom недоступны в Telegram.\n'
            + 'Введите адрес вашего кошелька вручную\n'
            + '(USDT TRC-20 / ETH / SOL):',
        buttons: [
            {type: 'default', text: '✏️ Ввести адрес', id: 'wallet_input'},
            {type: 'cancel', text: 'Отмена'}
        ]
    }, (btnId) => {
        if (btnId === 'wallet_input') {
            showWalletInput();
        }
    });
}

function showWalletInput() {
    tg.showPopup({
        title: '🔗 Адрес кошелька',
        message: 'Вставьте адрес вашего кошелька:',
        buttons: [
            {type: 'default', text: '📋 Вставить из буфера', id: 'paste_wallet'},
            {type: 'cancel', text: 'Назад'}
        ]
    }, async (btnId) => {
        if (btnId === 'paste_wallet') {
            try {
                const clipboardText = await navigator.clipboard.readText();
                if (clipboardText && clipboardText.length > 20) {
                    submitWallet(clipboardText.trim());
                } else {
                    tg.showPopup({
                        title: 'Введите адрес',
                        message: 'Буфер обмена пуст или содержит некорректный адрес.\nВведите адрес вручную:',
                        buttons: [
                            {type: 'default', text: '📝 Ввести', id: 'manual'},
                            {type: 'cancel', text: 'Отмена'}
                        ]
                    });
                }
            } catch(e) {
                // Clipboard not available, show manual input
                tg.showAlert('Буфер обмена недоступен. Используйте команду /wallet в чате с ботом.');
            }
        }
    });
}

function submitWallet(address) {
    if (!address || address.length < 20) {
        tg.showAlert('❌ Некорректный адрес кошелька.');
        return;
    }

    // Send to bot via sendData
    try {
        tg.sendData(JSON.stringify({
            action: 'wallet_connect',
            wallet: address
        }));
        tg.showAlert('✅ Адрес отправлен боту. Кошелёк будет привязан к вашему профилю.');
    } catch(e) {
        tg.showAlert('❌ Ошибка отправки. Используйте команду /wallet в чате с ботом.');
    }
}

// Main button
tg.MainButton.setText("ЗАКРЫТЬ");
tg.MainButton.show();
tg.MainButton.onClick(() => {
    tg.close();
});
