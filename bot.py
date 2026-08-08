import os
import time
import requests

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@ucuz_turboaz"

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL,
        "text": text
    }
    response = requests.post(url, data=data)
    print(response.text)

if __name__ == "__main__":
    send_message(
        "🤖 Ucuz Turbo AZ botu aktivdir!\n\n"
        "✅ Telegram bağlantısı uğurla yoxlanıldı.\n"
        "📉 Ucuz elan həddi: 20%"
    )

    while True:
        time.sleep(60)
