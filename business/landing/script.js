function toggleChat() {
    const chatbot = document.getElementById('lia-chatbot');
    chatbot.classList.toggle('chatbot-open');
}

function sendOption(option) {
    appendMessage(option, 'user');
    
    setTimeout(() => {
        let response = "";
        if (option === 'Узнать об услугах') {
            response = "Мы внедряем автономных AI-агентов для маркетинга, продаж и аналитики. Наш стек базируется на RTX 5090 и проприетарных протоколах Stab.";
        } else if (option === 'Заказать аудит') {
            response = "Отлично! Для глубокого аудита вашей IT-инфраструктуры мне понадобится ваш email. Введите его в поле ниже.";
        } else if (option === 'Связаться с шефом') {
            response = "Шеф сейчас на связи с ядром Synapse. Оставьте ваше сообщение, и я передам его немедленно по защищенному каналу.";
        }
        appendMessage(response, 'bot');
    }, 1000);
}

function sendMessage() {
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (text === "") return;

    appendMessage(text, 'user');
    input.value = "";

    setTimeout(() => {
        const response = "Информация получена. Протокол Stab синхронизирует данные. Мы свяжемся с вами в течение 10 минут.";
        appendMessage(response, 'bot');
    }, 1200);
}

function appendMessage(text, side) {
    const container = document.getElementById('chat-messages');
    const msg = document.createElement('div');
    msg.className = `msg ${side}`;
    msg.innerText = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

// Handle Enter key
document.getElementById('user-input')?.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
