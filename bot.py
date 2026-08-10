import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
SERPER_API_KEY = os.environ["SERPER_API_KEY"]

CHANNEL = "@ucuz_turboaz"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHANNEL,
            "text": text
        },
        timeout=30
    )


def main():

    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "q": "site:turbo.az/autos",
        "gl": "az",
        "hl": "az",
        "num": 30
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=30
    )

    print("SERPER STATUS:", response.status_code)
    print("SERPER RESPONSE:")
    print(response.text)

    if response.status_code != 200:
        send_message(
            "❌ Serper xətası:\n\n"
            + response.text[:3000]
        )
        return

    result = response.json()

    organic = result.get("organic", [])

    print("NƏTİCƏ SAYI:", len(organic))

    if not organic:
        send_message(
            "❌ Serper Turbo.az-dan nəticə qaytarmadı."
        )
        return

    message = (
        f"🔎 Serper Turbo.az-dan "
        f"{len(organic)} nəticə qaytardı.\n\n"
    )

    for i, item in enumerate(organic[:10], 1):

        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")

        message += (
            f"{i}. {title}\n"
            f"{snippet}\n"
            f"{link}\n\n"
        )

    send_message(message)


if __name__ == "__main__":
    main()
