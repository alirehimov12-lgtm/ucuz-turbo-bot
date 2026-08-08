import os
import requests

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@ucuz_turboaz"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {
    "chat_id": CHANNEL,
    "text": (
        "🤖 Ucuz Turbo AZ botu aktivdir!\n\n"
        "✅ Telegram bağlantısı uğurla yoxlanıldı.\n"
        "📉 Ucuz elan həddi: 20%"
    )
}

response = requests.post(url, data=data, timeout=20)

print(response.status_code)
print(response.text)
