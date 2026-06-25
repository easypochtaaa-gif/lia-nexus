import urllib.request
import json

tokens = [
    "8752434873:AAEwUJML4j1jQa9xWrLPE9KmioKDGhgwC9A",
    "8752434873:AAGvefmNxxFmxRKLbaafhqoYXhNS0jZY6Y0",
    "8752434873:AAHFMfA-YUztlhID5EpxFwiZ9WU2OQvHDPo",
    "8688389241:AAE_1loIVaQlkqFGwJsD1K8NLVdDBkE4608"
]

for t in tokens:
    print(f"\n--- Checking Token: {t} ---")
    try:
        url_me = f"https://api.telegram.org/bot{t}/getMe"
        req = urllib.request.Request(url_me)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("getMe output:")
            print(json.dumps(data, indent=2))
        
        # getWebhookInfo
        url_wh = f"https://api.telegram.org/bot{t}/getWebhookInfo"
        req_wh = urllib.request.Request(url_wh)
        with urllib.request.urlopen(req_wh) as response:
            data = json.loads(response.read().decode())
            print("getWebhookInfo output:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error checking token {t}: {e}")
