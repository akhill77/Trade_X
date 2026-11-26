import os, time, requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = {
    "BTC": "BTCUSD",
    "ETH": "ETHUSD",
    "SOL": "SOLUSD",
    "GOLD": "XAUUSD",
}

BASE = "https://api.india.delta.exchange"

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print("Telegram Error", e)

def get_ema(prices, period):
    k = 2 / (period + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = p * k + ema * (1 - k)
    return ema

def get_data(symbol):
    end = int(time.time())
    start = end - (100 * 3600)
    url = f"{BASE}/v2/history/candles"
    params = {"symbol": symbol, "resolution": "1h", "start": start, "end": end}
    r = requests.get(url, params=params, timeout=15).json()
    candles = r if isinstance(r, list) else r.get("result", [])
    if len(candles) < 20:
        raise Exception(f"Candle kam aayi {symbol} - {len(candles)}")
    closes = [float(c["close"]) for c in candles[:-1]]
    t = requests.get(f"{BASE}/v2/tickers/{symbol}", timeout=10).json()
    live_price = float(t["result"]["close"])
    return closes, live_price

def check_one(name, symbol):
    closes, live_price = get_data(symbol)
    live_closes = closes + [live_price]
    ema9 = get_ema(live_closes, 9)
    ema15 = get_ema(live_closes, 15)
    return live_price, ema9, ema15

send("✅ TradeX LIVE ON - Delta 1H\nEMA 9/15 Cross - Live Check 5 sec\nBTC, ETH, SOL, GOLD")

last_state = {}

while True:
    for name, sym in SYMBOLS.items():
        try:
            price, e9, e15 = check_one(name, sym)
            state = "UP" if e9 > e15 else "DOWN"
            prev = last_state.get(name)
            if prev is None:
                last_state[name] = state
                print(f"{name} START {state} Price:{price}")
                continue
            if prev != state:
                side = "BUY 🟢 CROSS UP" if state == "UP" else "SELL 🔴 CROSS DOWN"
                send(f"🚨 {name} LIVE CROSS 1H\n{side}\nPrice: {price}\nEMA 9 ne 15 ko kaata - Delta Live")
                print(f"ALERT SENT {name} {side} {price}")
                last_state[name] = state
            else:
                print(f"{name} No Cross Price:{price} EMA9:{e9:.2f} EMA15:{e15:.2f}")
        except Exception as e:
            print("Error", name, e)
    time.sleep(5)
