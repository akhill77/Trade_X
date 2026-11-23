import os, time, hmac, hashlib, requests, json
from datetime import datetime

# ===== PERMANENT LOCKED - BTC 350/250 | ETH 8/8 | GOLD 8/8 | 100% | 25x | 9/15 =====
API_KEY = os.getenv("DELTA_API_KEY")
API_SECRET = os.getenv("DELTA_API_SECRET")
BASE_URL = "https://api.india.delta.exchange"
SYMBOLS = {"BTCUSD": "BTC", "ETHUSD": "ETH", "XAUUSD": "GOLD"}
TP_SL = {"BTCUSD": {"target": 350, "sl": 250}, "ETHUSD": {"target": 8, "sl": 8}, "XAUUSD": {"target": 8, "sl": 8}}
LEVERAGE = 25
TIMEFRAME = "1h"
last_signal = {}
open_trade = {}

def get_headers(method, path, body=""):
    timestamp = str(int(time.time()))
    signature_data = method + timestamp + path + body
    signature = hmac.new(API_SECRET.encode(), signature_data.encode(), hashlib.sha256).hexdigest()
    return {"api-key": API_KEY, "timestamp": timestamp, "signature": signature, "Content-Type": "application/json"}

def get_balance():
    try:
        r = requests.get(BASE_URL + "/v2/wallet/balances", headers=get_headers("GET", "/v2/wallet/balances"), timeout=5)
        for w in r.json().get("result", []):
            if w["asset_symbol"] == "USDT":
                return float(w["available_balance"])
    except Exception as e:
        print("Balance Error:", e)
    return 0

def get_candles(symbol):
    try:
        url = f"{BASE_URL}/v2/history/candles?symbol={symbol}&resolution={TIMEFRAME}&limit=50"
        r = requests.get(url, timeout=5)
        return [float(c["close"]) for c in r.json().get("result", [])]
    except: return []

def ema(data, period):
    if len(data) < period: return None
    k = 2 / (period + 1)
    e = data[0]
    for price in data[1:]:
        e = price * k + e * (1 - k)
    return e

def get_position(symbol):
    try:
        r = requests.get(BASE_URL + f"/v2/positions?product_symbol={symbol}", headers=get_headers("GET", f"/v2/positions?product_symbol={symbol}"), timeout=5)
        pos = r.json().get("result", [])
        if pos and float(pos[0].get("size", 0)) != 0:
            return pos[0]
    except: pass
    return None

def place_order(symbol, side, size, reduce_only=False):
    try:
        requests.post(BASE_URL + "/v2/products/set_leverage", headers=get_headers("POST", "/v2/products/set_leverage", json.dumps({"product_symbol": symbol, "leverage": str(LEVERAGE)})), json={"product_symbol": symbol, "leverage": str(LEVERAGE)}, timeout=5)
        body = json.dumps({"product_symbol": symbol, "size": str(int(size)), "side": side, "order_type": "market_order", "time_in_force": "gtc", "reduce_only": str(reduce_only).lower()})
        r = requests.post(BASE_URL + "/v2/orders", headers=get_headers("POST", "/v2/orders", body), data=body, timeout=5)
        print(f"ORDER {symbol} {side} {size} ->", r.json())
    except Exception as e:
        print("Order Error:", e)

def close_position(symbol, reason=""):
    pos = get_position(symbol)
    if pos:
        print(f"Closing {symbol} - Reason: {reason}")
        size = abs(float(pos["size"]))
        side = "sell" if float(pos["size"]) > 0 else "buy"
        place_order(symbol, side, size, reduce_only=True)
        if symbol in open_trade:
            del open_trade[symbol]

def check_tp_sl(symbol, live_price):
    if symbol not in open_trade: return False
    t = open_trade[symbol]
    tp = TP_SL[symbol]["target"]
    sl = TP_SL[symbol]["sl"]
    if t["side"] == "BUY":
        if live_price >= t["target_price"]:
            print(f"TARGET HIT {symbol} Entry {t['entry']} -> {live_price} (+{tp}$)")
            close_position(symbol, f"TARGET {tp}$ HIT")
            return True
        if live_price <= t["sl_price"]:
            print(f"SL HIT {symbol} Entry {t['entry']} -> {live_price} (-{sl}$)")
            close_position(symbol, f"SL {sl}$ HIT")
            return True
    else:
        if live_price <= t["target_price"]:
            print(f"TARGET HIT {symbol} Entry {t['entry']} -> {live_price} (+{tp}$)")
            close_position(symbol, f"TARGET {tp}$ HIT")
            return True
        if live_price >= t["sl_price"]:
            print(f"SL HIT {symbol} Entry {t['entry']} -> {live_price} (-{sl}$)")
            close_position(symbol, f"SL {sl}$ HIT")
            return True
    return False

def check_and_trade(symbol):
    closes = get_candles(symbol)
    if len(closes) < 20: return
    live_price = closes[-1]
    if check_tp_sl(symbol, live_price):
        last_signal[symbol] = None
        return
    ema9 = ema(closes, 9)
    ema15 = ema(closes, 15)
    ema9_prev = ema(closes[:-1], 9)
    ema15_prev = ema(closes[:-1], 15)
    signal = None
    if ema9_prev <= ema15_prev and ema9 > ema15:
        signal = "BUY"
    elif ema9_prev >= ema15_prev and ema9 < ema15:
        signal = "SELL"
    if signal and last_signal.get(symbol) != signal:
        print(f"CROSS {symbol} {signal} | EMA9 {ema9:.2f} EMA15 {ema15:.2f} Price {live_price}")
        last_signal[symbol] = signal
        close_position(symbol, "OPPOSITE CROSS - B MODE")
        time.sleep(0.5)
        balance = get_balance()
        if balance > 5:
            qty = (balance * LEVERAGE) / live_price
            if symbol == "XAUUSD": qty = int(qty)
            else: qty = int(qty * 1000) / 1000
            if qty > 0:
                side = "buy" if signal == "BUY" else "sell"
                place_order(symbol, side, qty)
                tp = TP_SL[symbol]["target"]
                sl = TP_SL[symbol]["sl"]
                if signal == "BUY":
                    target_price = live_price + tp
                    sl_price = live_price - sl
                else:
                    target_price = live_price - tp
                    sl_price = live_price + sl
                open_trade[symbol] = {"side": signal, "entry": live_price, "target_price": target_price, "sl_price": sl_price}
                print(f"TRADE LOCKED {symbol} {signal} Entry {live_price} Target {target_price} SL {sl_price}")

print("Trade_X Bot Started - LOCKED TP/SL | 100% | 25x | 9/15 Cross")
while True:
    try:
        for sym in SYMBOLS:
            check_and_trade(sym)
    except Exception as e:
        print("Loop Error:", e)
    time.sleep(1)
