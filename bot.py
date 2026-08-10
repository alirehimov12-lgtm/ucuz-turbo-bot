import os
import re
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
SERPER_API_KEY = os.environ["SERPER_API_KEY"]

CHANNEL = "@ucuz_turboaz"

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def search_turbo(query):
    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "q": f"site:turbo.az/autos {query}",
        "gl": "az",
        "hl": "az",
        "num": 10
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=30
    )

    response.raise_for_status()
    return response.json()


def get_price(text):
    if not text:
        return None

    # 30 500 AZN / 30,500 AZN / 30500 AZN
    matches = re.findall(
        r'(\d{1,3}(?:[ .,\s]\d{3})+|\d{4,6})\s*(?:AZN|azn|manat)',
        text
    )

    prices = []

    for value in matches:
        value = re.sub(r"[ .,\s]", "", value)

        try:
            price = int(value)

            if 500 <= price <= 500000:
                prices.append(price)
        except:
            pass

    return prices[0] if prices else None


def get_cars(query):
    result = search_turbo(query)

    cars = []

    for item in result.get("organic", []):
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")

        if "turbo.az" not in link:
            continue

        text = title + " " + snippet

        price = get_price(text)

        if price:
            cars.append({
                "title": title,
                "price": price,
                "snippet": snippet,
                "link": link
            })

    return cars


def send_message(text):
    data = {
        "chat_id": CHANNEL,
        "text": text,
        "disable_web_page_preview": False
    }

    response = requests.post(
        TELEGRAM_URL,
        data=data,
        timeout=30
    )

    print(response.status_code)
    print(response.text)


def main():

    # Test axtarış
    cars = get_cars("BMW 520")

    print("Tapılan elan sayı:", len(cars))

    for car in cars:
        message = (
            "🚗 TURBO.AZ ELANI\n\n"
            f"📌 {car['title']}\n"
            f"💰 Qiymət: {car['price']:,} AZN\n\n"
            f"{car['snippet']}\n\n"
            f"🔗 {car['link']}"
        )

        send_message(message)


if __name__ == "__main__":
    main()
