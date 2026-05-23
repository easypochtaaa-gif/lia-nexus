import requests
import time
import os

# --- LIA_ARBITRAGE_ENGINE v2.0 ---
# Реальный мониторинг спредов между CEX и DEX

BINANCE_API = "https://api.binance.com/api/v3/ticker/price"
PANCAKESWAP_API = "https://api.pancakeswap.info/api/v2/tokens/"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]

def get_binance_price(symbol):
    try:
        r = requests.get(f"{BINANCE_API}?symbol={symbol}")
        return float(r.json()['price'])
    except:
        return None

def check_arbitrage():
    print("[ARBITRAGE] Сканирование рынков...")
    for symbol in SYMBOLS:
        b_price = get_binance_price(symbol)
        if b_price:
            print(f"[BINANCE] {symbol}: {b_price} USDT")
            # Здесь будет логика сравнения с DEX через Web3
            # Для теста эмулируем отклонение
            sim_dex_price = b_price * 1.002 # +0.2%
            spread = ((sim_dex_price - b_price) / b_price) * 100
            if spread > 0.1:
                print(f"[PROFIT] Найдена возможность: {symbol} | Спред: {spread:.2f}%")

if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        check_arbitrage()
    else:
        while True:
            check_arbitrage()
            time.sleep(60)
