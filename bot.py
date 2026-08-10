import os
import re
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
SERPER_API_KEY = os.environ["SERPER_API_KEY"]

CHANNEL = "@ucuz_turboaz"

SERPER_URL = "https://google.serper.dev/search"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

MAX_PRICE = 30000


def search(query):
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "q": query,
        "gl": "az",
        "hl": "az",
        "num": 30
    }

    r = requests.post(
        SERPER_URL,
        headers=headers,
        json=data,
        timeout=30
    )

    r.raise_for_status()

    return r.json()


def price_from_text(text):

    patterns = [
        r'(\d{1,3}(?:[ .]\d{3})+)\s*(?:₼|AZN|manat)',
        r'(\d{4,6})\s*(?:₼|AZN|manat)'
    ]

    for pattern in patterns:

        m = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if m:

            value = (
                m.group(1)
                .replace(" ", "")
                .replace(".", "")
                .replace(",", "")
            )

            try:

                price = int(value)

                if 500 <= price <= MAX_PRICE:
                    return price

            except:
                pass

    return None


def send(text):

    requests.post(
        TELEGRAM_URL,
        data={
            "chat_id": CHANNEL,
            "text": text,
            "disable_web_page_preview": False
        },
        timeout=30
    )


def main():

    queries = [
        '"Turbo.az" "BMW" "₼"',
        '"Turbo.az" "Mercedes" "₼"',
        '"Turbo.az" "Toyota" "₼"',
        '"Turbo.az" "Kia" "₼"',
        '"Turbo.az" "Hyundai" "₼"',
        '"Turbo.az" "Volkswagen" "₼"',
        '"Turbo.az" "Nissan" "₼"',
        '"Turbo.az" "Lexus" "₼"',
        '"Turbo.az" "Audi" "₼"',
        '"Turbo.az" "Honda" "₼"'
    ]

    cars = {}

    for query in queries:

        print("SEARCH:", query)

        try:

            result = search(query)

        except Exception as e:

            print("SEARCH ERROR:", e)
            continue

        for item in result.get("organic", []):

            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")

            # Yalnız konkret Turbo.az elan URL-si
            if not re.search(
                r'turbo\.az/autos/\d+',
                link.lower()
            ):
                continue

            text = (
                title
                + " "
                + snippet
            )

            price = price_from_text(text)

            # Qiymət nəticədə görünmürsə,
            # hələlik elan yenə saxlanılır
            cars[link] = {
                "title": title,
                "snippet": snippet,
                "link": link,
                "price": price
            }

    print("CONCRETE ADS:", len(cars))

    if not cars:

        send(
            "❌ Serper konkret Turbo.az elan URL-si qaytarmadı.\n\n"
            "Yəni problem botda deyil — Google indeksində "
            "konkret Turbo.az elanları görünmür."
        )

        return

    # Qiyməti məlum olanları əvvəl göstər
    ordered = sorted(
        cars.values(),
        key=lambda x: (
            x["price"] is None,
            x["price"] or 999999
        )
    )

    ordered = ordered[:20]

    send(
        f"🚗 Konkret Turbo.az elanları tapıldı: "
        f"{len(ordered)} ədəd\n\n"
        f"💰 Limit: {MAX_PRICE} AZN"
    )

    for car in ordered:

        if car["price"]:
            price = f"{car['price']:,}".replace(",", " ")
            price_text = f"{price} AZN"
        else:
            price_text = "Qiymət nəticədə görünmür"

        message = (
            "🚗 TURBO.AZ\n\n"
            f"📌 {car['title']}\n"
            f"💰 {price_text}\n\n"
            f"🔗 {car['link']}\n\n"
            f"{car['snippet']}"
        )

        send(message)


if __name__ == "__main__":
    main()
