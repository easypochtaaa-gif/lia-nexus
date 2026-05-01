#!/bin/bash
# LIA // IMPERIAL VISUAL CORE DEPLOYMENT
# Target: NVIDIA A100 CLUSTER

echo "--- INITIALIZING VISUAL CORE DEPLOYMENT ---"

# 1. Update and install dependencies
sudo apt update && sudo apt install -y python3-venv libgl1 libglib2.0-0 wget git

# 2. Clone Stable Diffusion WebUI (Automatic1111)
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui

# 3. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 4. Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# 5. Download Imperial Weights (SDXL Base)
mkdir -p models/Stable-diffusion
wget -O models/Stable-diffusion/sd_xl_base_1.0.safetensors https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors

# 6. Launch API Mode
# We run it with --api for our bot to connect and --listen for remote access
export COMMANDLINE_ARGS="--api --listen --xformers --enable-insecure-extension-access --no-half-vae"
python3 launch.py
