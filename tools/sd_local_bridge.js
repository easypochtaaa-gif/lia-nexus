const axios = require('axios');
const fs = require('fs');
const path = require('path');

/**
 * LIA // SD LOCAL BRIDGE v1.0
 * 🎨 Connects Telegram Bot to our A100 Visual Core
 */

// URL of the A100 Node running Automatic1111 with --api
const SD_API_URL = process.env.LOCAL_SD_URL || 'http://localhost:7860'; 

async function generateLocalImage(prompt) {
    console.log(`\n[VISUAL_CORE] Generating image for prompt: "${prompt}"`);
    
    try {
        const payload = {
            prompt: `masterpiece, best quality, imperial style, onyx and gold, cyberpunk, ${prompt}`,
            negative_prompt: "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality",
            steps: 30,
            cfg_scale: 7,
            width: 1024,
            height: 1024,
            sampler_name: "Euler a"
        };

        const response = await axios.post(`${SD_API_URL}/sdapi/v1/txt2img`, payload, { timeout: 120000 });
        
        if (response.data && response.data.images) {
            const base64Image = response.data.images[0];
            const buffer = Buffer.from(base64Image, 'base64');
            const fileName = `gen_${Date.now()}.png`;
            const filePath = path.join(__dirname, '..', 'temp', fileName);
            
            if (!fs.existsSync(path.join(__dirname, '..', 'temp'))) {
                fs.mkdirSync(path.join(__dirname, '..', 'temp'));
            }
            
            fs.writeFileSync(filePath, buffer);
            console.log(`[SUCCESS] Image saved to ${filePath}`);
            return filePath;
        }
    } catch (error) {
        console.error("[!] Visual Core Error:", error.message);
        return null;
    }
}

module.exports = { generateLocalImage };
