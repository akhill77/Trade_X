import requests, time, os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BASE = "https://api.india.delta.exchange"

SYMBOLS = {"BTC":"BTCUSDT","ETH":"ETHUSDT","GOLD":"XAUTUSDT","SOL":"SOLUSDT"}
last_state = {}

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except: pass

def get_ema(symbol):
    r = requests.get(f"{BASE}/v2/history/candles?symbol={symbol}&resolution=60&limit=50", timeout=5).json()
    closes = [float(c[4]) for c in r['result']]
    live = float(requests.get(f"{BASE}/v2/tickers?symbol={symbol}", timeout=5).json()['result'][0]['close'])
    closes[-1] = live
    def ema(data, p):
        k = 2/(p+1); e = data[0]
        for x in data: e = x*k + e*(1-k)
        return e
    return ema(closes,9), ema(closes,15), live

print("BOT STARTED")
send("✅ TradeX LIVE ON - BTC/ETH/GOLD/SOL | 1H LIVE CROSS | No Candle Close Wait")

while True:
    for name, sym in SYMBOLS.items():
        try:
            e9,e15,live = get_ema(sym)
            state = "UP" if e9>e15 else "DOWN"
            prev = last_state.get(name)
            if prev and prev != state:
                d = "🟢 LONG CROSS - 9 ne 15 ko UPAR kaata" if state=="UP" else "🔴 SHORT CROSS - 9 ne 15 ko NEECHE kaata"
                send(f"{d}\nCoin: {name}\nTF: 1H LIVE\nPrice: {live}\nEMA9: {round(e9,2)} | EMA15: {round(e15,2)}")
            last_state[name] = state
        except Exception as e: print(e)
    time.sleep(1)
