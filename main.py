import os, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is Live!")
        def log_message(self, *a): pass
    HTTPServer(("0.0.0.0", port), H).serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

print("Trade_X Bot Started...")
while True:
    print("Bot is alive... checking market")
    time.sleep(60)
