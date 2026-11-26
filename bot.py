import os, threading, time, requests, yfinance as yf
from flask import Flask

# --- Flask - Render ke liye Port kholne ke liye ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live"

# --- Telegram Settings - Yaha apna daal dena ---
TELEGRAM_TOKEN = "APNA_TOKEN_YAHA_DALO"
CHAT_ID = "APNA_CHAT_ID_YAHA_DALO"

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Telegram Error:", e)

def bot_loop():
    send_msg("✅ Bot LIVE ho gaya hai - Render pe chal raha hai")
    while True:
        try:
            # Example: Nifty ka price check
            data = yf.Ticker("^NSEI").history(period="1d", interval="1m")
            price = round(data['Close'].iloc[-1], 2)
            print("Nifty Price:", price)
        except Exception as e:
            print("Bot Error:", e)
        time.sleep(300)  # 5 min baad fir check karega

# --- Bot ko alag thread me chalao + Flask ko Port pe chalao ---
threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
