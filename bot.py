import os, threading
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live"

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
