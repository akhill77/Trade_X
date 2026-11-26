import os, threading, time, requests, yfinance as yf
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# --- Render ko Port dene ke liye (Isse Live hoga) ---
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

PORT = int(os.environ.get('PORT', 10000))
threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), H).serve_forever(), daemon=True).start()

# --- Telegram ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID', '8495049377')

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        print("Sent:", msg)
    except Exception as e:
        print("Telegram Error:", e)

# --- Bot Start ---
send("✅ TradeX LIVE ON...\nBot chalu ho gaya hai, ab notification aayenge!")
print("Bot Started, Port:", PORT)

last_price = 0
while True:
    try:
        # Nifty 50 ka live price
        data = yf.Ticker("^NSEI").history(period="1d", interval="1m")
        if not data.empty:
            price = round(float(data['Close'].iloc[-1]), 2)
            now = datetime.now().strftime("%H:%M:%S")
            print(f"{now} NIFTY: {price}")

            # Agar price badla to hi message bhejo (spam nahi hoga)
            if abs(price - last_price) > 20:
                send(f"📈 NIFTY Update: {price}\nTime: {now}")
                last_price = price
        else:
            print("Data empty, retry...")
    except Exception as e:
        print("Error:", e)

    time.sleep(60)
