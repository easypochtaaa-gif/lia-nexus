import os
import json
import requests
from datetime import datetime

# --- CONFIG ---
# We'll use OpenAI for high-quality marketing copy or Ollama if preferred
API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = "https://api.openai.com/v1/chat/completions"

# NEON FLOW Brand Identity
BRAND_PROMPT = """
Role: Marketing Specialist for NEON FLOW.
Style: Aggressive, cyberpunk, minimalist, result-oriented.
Target: Telegram channel owners, business owners, digital entrepreneurs.
Tone: Expert, slightly mysterious, absolute confidence.

Brand Message: We generate AI-driven content that captures attention and converts into money. 
No fluff. 10 posts in 24 hours. Minimal prices for early adopters.
"""

def generate_post(topic):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": BRAND_PROMPT},
            {"role": "user", "content": f"Generate a Telegram post about: {topic}. Use emojis, high-impact headlines, and a call to action to DM @username."}
        ],
        "temperature": 0.7
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"

def main():
    topics = [
        "NEON FLOW Activation - The launch of the ultimate AI content machine",
        "Why standard social media marketing is failing in 2026",
        "The 10 posts / 24 hours offer details (300 -> 500 -> 1000 UAH)",
        "Social Proof: How attention = currency",
        "Fear of missing out: Why your competitors are already using AI"
    ]
    
    print(f"--- NEON FLOW CONTENT BATCH [{datetime.now().strftime('%Y-%m-%d')}] ---")
    
    for i, topic in enumerate(topics, 1):
        print(f"\n[GENERATING POST {i}]...")
        content = generate_post(topic)
        print("-" * 30)
        print(content)
        print("-" * 30)
        
        # Save to file
        with open("neon_flow_posts.txt", "a", encoding="utf-8") as f:
            f.write(f"\n--- POST {i}: {topic} ---\n")
            f.write(content)
            f.write("\n\n")

if __name__ == "__main__":
    if not API_KEY:
        print("OPENAI_API_KEY not found in .env")
    else:
        main()
