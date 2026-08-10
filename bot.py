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

    queries = [
        "Turbo.az BMW 520",
        "Turbo.az Mercedes",
        "Turbo.az Toyota",
        "Turbo.az Kia",
        "Turbo.az Hyundai"
    ]

    all_results = []

    for query in queries:

        data = {
            "q": query,
            "gl": "az",
            "hl": "az",
            "num": 20
        }

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )

        print(query, response.status_code)

        if response.status_code != 200:
            print(response.text)
            continue

        result = response.json()

        for item in result.get("organic", []):

            link = item.get("link", "")

            if "turbo.az" in link.lower():
                all_results.append(item)

    # Təkrarları sil
    unique = {}

    for item in all_results:
        unique[item.get("link")] = item

    results = list(unique.values())

    print("Turbo.az nəticələri:", len(results))

    if not results:
        send_message(
            "❌ Bu dəfə Serper-dən Turbo.az nəticəsi gəlmədi."
        )
        return

    message = (
        f"🔎 Turbo.az nəticələri: {len(results)}\n\n"
    )

    for i, item in enumerate(results[:10], 1):

        message += (
            f"{i}. {item.get('title', '')}\n"
            f"{item.get('snippet', '')}\n"
            f"{item.get('link', '')}\n\n"
        )

    send_message(message)


if __name__ == "__main__":
    main()
