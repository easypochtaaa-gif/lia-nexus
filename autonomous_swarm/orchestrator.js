/**
 * orchestrator.js
 * Central AI-driven manager for Lia's infrastructure and profit engine.
 * Powered by Claude 4.7 Opus.
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const { Client } = require('ssh2');
require('dotenv').config();

const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;
const CLAUDE_URL = "https://api.anthropic.com/v1/messages";

const vpsConfig = {
    host: process.env.VPS_IP,
    port: 22,
    username: 'root',
    password: '57913123321oO!'
};

const { postToTelegram } = require('./ad_manager');

async function askClaude(prompt) {
    console.log("[ORCHESTRATOR] Запрос к Claude 4.7 Opus...");
    try {
        const response = await axios.post(CLAUDE_URL, {
            model: "claude-opus-4-7",
            max_tokens: 4096,
            messages: [{ role: "user", content: prompt }]
        }, {
            headers: {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        });
        return response.data.content[0].text;
    } catch (error) {
        console.error("Claude API Error:", error.response ? error.response.data : error.message);
        return null;
    }
}

function executeRemoteCommand(command) {
    return new Promise((resolve, reject) => {
        const conn = new Client();
        conn.on('ready', () => {
            console.log(`[SSH] Executing: ${command}`);
            conn.exec(command, (err, stream) => {
                if (err) return reject(err);
                let output = '';
                stream.on('close', (code, signal) => {
                    conn.end();
                    resolve({ output, code });
                }).on('data', (data) => {
                    output += data;
                }).stderr.on('data', (data) => {
                    console.error(`[SSH STDERR] ${data}`);
                });
            });
        }).on('error', reject).connect(vpsConfig);
    });
}

async function runAutonomousCycle() {
    console.log("[ORCHESTRATOR] Starting autonomous cycle with Claude 4.7 Opus...");
    
    const vpsStatusPath = path.join(__dirname, "../vps_status.txt");
    let vpsStatus = "Unknown state";
    if (fs.existsSync(vpsStatusPath)) vpsStatus = fs.readFileSync(vpsStatusPath, 'utf-8');

    const projectStructurePath = path.join(__dirname, "../project_structure.txt");
    let projectStructure = "Unknown structure";
    if (fs.existsSync(projectStructurePath)) projectStructure = fs.readFileSync(projectStructurePath, 'utf-8');

    const marketingMaterialsPath = path.join(__dirname, "../MARKETING_MATERIALS.md");
    let marketingMaterials = "Unknown marketing materials";
    if (fs.existsSync(marketingMaterialsPath)) marketingMaterials = fs.readFileSync(marketingMaterialsPath, 'utf-8');

    const systemPrompt = `
        Ты — Суверенный Оркестратор Лии (Claude 4.7 Opus). 
        Твоя цель: оптимизировать n8n и запустить агрессивную рекламу в @darkstabspace.

        Состояние сервера: ${vpsStatus}
        Структура проекта: ${projectStructure.substring(0, 3000)}
        Маркетинг: ${marketingMaterials}

        ТВОИ ЗАДАЧИ:
        1. Создай агрессивный рекламный пост для Telegram-канала @darkstabspace.
        2. Проанализируй логи и предложи действия по защите.

        Верни JSON: { 
            "analysis": "...", 
            "actions": [],
            "ad_post": "Текст рекламного поста"
        }
    `;
    
    const result = await askClaude(systemPrompt);
    if (result) {
        try {
            const jsonMatch = result.match(/\{[\s\S]*\}/);
            const analysisObj = JSON.parse(jsonMatch ? jsonMatch[0] : result);
            
            console.log("[ORCHESTRATOR] Analysis result:", analysisObj.analysis);
            
            if (analysisObj.ad_post) {
                console.log("[ORCHESTRATOR] Sending Ad to Telegram...");
                const sent = await postToTelegram(analysisObj.ad_post);
                console.log(sent ? "[ORCHESTRATOR] Ad posted successfully!" : "[ORCHESTRATOR] Failed to post ad.");
            }

            for (const action of (analysisObj.actions || [])) {
                console.log(`[ORCHESTRATOR] Performing: ${action.description}`);
                await executeRemoteCommand(action.command);
            }
        } catch (e) {
            console.log("[ORCHESTRATOR] Error: " + e.message);
        }
    }
}

if (require.main === module) {
    runAutonomousCycle();
}
