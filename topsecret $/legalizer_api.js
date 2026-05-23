const express = require('express');
const { exec } = require('child_process');
const app = express();
const port = 3005;

// --- LIA_LEGALIZER_SaaS_API ---
// API обертка над парсером Legalizer для продажи лидов

app.get('/api/leads/latest', (req, res) => {
    console.log('[API] Запрос на свежие лиды...');
    // Запускаем питоновский парсер для сбора данных
    exec('python legalizer_parser.py', (error, stdout, stderr) => {
        if (error) {
            return res.status(500).json({ error: 'Failed to run parser' });
        }
        // В реале мы бы читали из БД, тут для теста отдаем статус
        res.json({
            status: 'SUCCESS',
            message: 'Leads extracted and synced with Synapse Core',
            timestamp: new Date().toISOString()
        });
    });
});

app.listen(port, () => {
    console.log(`🚀 LEGALIZER_API запущен на порту ${port}`);
});
