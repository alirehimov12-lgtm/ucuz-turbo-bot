import os
import re
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
SERPER_API_KEY = os.environ["SERPER_API_KEY"]

CHANNEL = "@ucuz_turboaz"

SERPER_URL = "https://google.serper.dev/search"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

MAX_PRICE = 30000
MAX_SEND = 20


def search_google(query):
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

    response = requests.post(
        SERPER_URL,
        headers=headers,
        json=data,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def extract_price(text):

    if not text:
        return None

    patterns = [
        r'(\d{1,3}(?:[ .]\d{3})+)\s*(?:AZN|azn|₼|manat)',
        r'(\d{4,6})\s*(?:AZN|azn|₼|manat)',
        r'(\d{1,3}(?:[ .]\d{3})+)\s*₼',
        r'(\d{4,6})\s*₼'
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        value = match.group(1)

        value = (
            value
            .replace(" ", "")
            .replace(".", "")
            .replace(",", "")
        )

        try:

            price = int(value)

            if 500 <= price <= MAX_PRICE:
                return price

        except ValueError:
            pass

    return None


def extract_year(text):

    if not text:
        return None

    years = re.findall(
        r'\b(19\d{2}|20\d{2})\b',
        text
    )

    for value in years:

        year = int(value)

        if 1980 <= year <= 2026:
            return year

    return None


def extract_km(text):

    if not text:
        return None

    patterns = [
        r'([\d .]+)\s*km',
        r'([\d .]+)\s*KM'
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        value = match.group(1)

        value = (
            value
            .replace(" ", "")
            .replace(".", "")
            .replace(",", "")
        )

        try:
            return int(value)

        except ValueError:
            pass

    return None


def get_cars(query):

    data = search_google(query)

    cars = []

    for item in data.get("organic", []):

        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")

        # Yalnız Turbo.az elanları
        if "turbo.az/autos/" not in link:
            continue

        text = (
            title
            + " "
            + snippet
        )

        price = extract_price(text)

        # Qiymət tapılmadısa keç
        if price is None:
            continue

        # 30 000 AZN-dən baha keçmə
        if price > MAX_PRICE:
            continue

        year = extract_year(text)

        km = extract_km(text)

        cars.append({
            "title": title,
            "snippet": snippet,
            "link": link,
            "price": price,
            "year": year,
            "km": km
        })

    return cars


def send_telegram(message):

    data = {
        "chat_id": CHANNEL,
        "text": message,
        "disable_web_page_preview": False
    }

    response = requests.post(
        TELEGRAM_URL,
        data=data,
        timeout=30
    )

    response.raise_for_status()


def main():

    queries = [

        'site:turbo.az/autos/ "AZN" "km" avtomobil',

        'site:turbo.az/autos/ "AZN" "km" BMW',

        'site:turbo.az/autos/ "AZN" "km" Mercedes',

        'site:turbo.az/autos/ "AZN" "km" Toyota',

        'site:turbo.az/autos/ "AZN" "km" Hyundai',

        'site:turbo.az/autos/ "AZN" "km" Kia',

        'site:turbo.az/autos/ "AZN" "km" Volkswagen',

        'site:turbo.az/autos/ "AZN" "km" Nissan',

        'site:turbo.az/autos/ "AZN" "km" Lexus',

        'site:turbo.az/autos/ "AZN" "km" Honda',

        'site:turbo.az/autos/ "AZN" "km" Ford',

        'site:turbo.az/autos/ "AZN" "km" Audi'
    ]

    all_cars = []

    for query in queries:

        try:

            print("Axtarılır:", query)

            cars = get_cars(query)

            print(
                "Tapılan:",
                len(cars)
            )

            all_cars.extend(cars)

        except Exception as error:

            print(
                "Axtarış xətası:",
                error
            )

    # Eyni elanları silirik
    unique = {}

    for car in all_cars:

        unique[
            car["link"]
        ] = car

    cars = list(
        unique.values()
    )

    print(
        "Təkrarsız elan sayı:",
        len(cars)
    )

    if not cars:

        send_telegram(
            "🔎 30 000 AZN-ə qədər "
            "Turbo.az elanı tapılmadı."
        )

        return

    # Ucuzdan bahaya sırala
    cars.sort(
        key=lambda car: car["price"]
    )

    # Maksimum 20 elan
    cars = cars[:MAX_SEND]

    send_telegram(
        f"🔎 Turbo.az-dan "
        f"{len(cars)} uyğun elan tapıldı.\n\n"
        f"💰 Maksimum qiymət: "
        f"{MAX_PRICE:,} AZN".replace(",", " ")
    )

    for car in cars:

        price = (
            f"{car['price']:,}"
            .replace(",", " ")
        )

        if car["year"]:
            year = str(
                car["year"]
            )
        else:
            year = "Məlum deyil"

        if car["km"]:
            km = (
                f"{car['km']:,}"
                .replace(",", " ")
                + " km"
            )
        else:
            km = "Məlum deyil"

        message = (
            "🚗 TURBO.AZ ELANI\n\n"

            f"📌 {car['title']}\n\n"

            f"💰 Qiymət: "
            f"{price} AZN\n"

            f"📅 İl: "
            f"{year}\n"

            f"🛣 Yürüş: "
            f"{km}\n\n"

            f"🔗 {car['link']}\n\n"

            "💡 Limit: 30 000 AZN"
        )

        try:

            send_telegram(
                message
            )

        except Exception as error:

            print(
                "Telegram xətası:",
                error
            )


if __name__ == "__main__":
    main()
