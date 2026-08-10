import os
import re
import statistics
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
SERPER_API_KEY = os.environ["SERPER_API_KEY"]

CHANNEL = "@ucuz_turboaz"

SERPER_URL = "https://google.serper.dev/search"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

MAX_PRICE = 30000
SEARCH_RESULTS = 30

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


def search_google(query):
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "q": query,
        "gl": "az",
        "hl": "az",
        "num": SEARCH_RESULTS
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
        r'(\d{1,3}(?:[ .]\d{3})+)\s*(?:AZN|₼|manat)',
        r'(\d{4,6})\s*(?:AZN|₼|manat)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            value = match.group(1)
            value = value.replace(" ", "").replace(".", "")

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

    years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)

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
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            value = match.group(1)
            value = value.replace(" ", "").replace(".", "")

            try:
                return int(value)

            except ValueError:
                pass

    return None


def is_active(url):
    """
    Turbo.az elan səhifəsinin açılıb-açılmadığını yoxlayır.
    Sərt mətn yoxlaması etmir ki, aktiv elanları səhvən silməsin.
    """

    try:
        response = session.get(
            url,
            timeout=20,
            allow_redirects=True
        )

        print("ACTIVE CHECK:",
              response.status_code,
              response.url)

        if response.status_code != 200:
            return False

        if "turbo.az" not in response.url.lower():
            return False

        if "/autos/" not in response.url.lower():
            return False

        return True

    except Exception as error:
        print("Aktivlik yoxlama xətası:", error)
        return False


def get_cars(query):
    data = search_google(query)

    cars = []

    for item in data.get("organic", []):

        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")

        if "turbo.az/autos/" not in link:
            continue

        text = f"{title} {snippet}"

        price = extract_price(text)

        if price is None:
            continue

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


def calculate_market_price(cars):
    prices = [
        car["price"]
        for car in cars
        if 500 <= car["price"] <= MAX_PRICE
    ]

    if len(prices) < 3:
        return None

    return statistics.median(prices)


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
        'site:turbo.az/autos/ "AZN" "km"',
        'site:turbo.az/autos/ "₼" "km"',
        'site:turbo.az/autos/ "manat" "km"',
        'site:turbo.az/autos/ "2026" "AZN"',
        'site:turbo.az/autos/ "2025" "AZN"'
    ]

    all_cars = []

    for query in queries:

        try:
            print("Axtarılır:", query)

            cars = get_cars(query)

            print("Tapıldı:", len(cars))

            all_cars.extend(cars)

        except Exception as error:
            print("Axtarış xətası:", error)

    # Təkrar elanları sil
    unique_cars = {}

    for car in all_cars:
        unique_cars[car["link"]] = car

    cars = list(unique_cars.values())

    print("Təkrarsız elan:", len(cars))

    if not cars:
        send_telegram(
            "🔎 30 000 AZN-ə qədər Turbo.az elanı tapılmadı."
        )
        return

    # Aktivlik yoxlaması
    active_cars = []

    for car in cars:

        print("Elan yoxlanılır:")
        print(car["link"])

        if is_active(car["link"]):
            active_cars.append(car)

    print("Aktiv elan sayı:", len(active_cars))

    if not active_cars:
        send_telegram(
            "⚠️ Turbo.az nəticələri tapıldı, "
            "amma aktivlik yoxlamasından heç biri keçmədi."
        )
        return

    # Bütün aktiv elanların bazar medianı
    market = calculate_market_price(active_cars)

    print("Bazar medianı:", market)

    # Hazırda bütün 30 000 AZN-ə qədər aktiv elanları göndəririk.
    # Sonrakı mərhələdə model üzrə ayrıca bazar qiyməti hesablayacağıq.

    active_cars.sort(
        key=lambda car: car["price"]
    )

    # Maksimum 10 elan
    selected = active_cars[:10]

    for car in selected:

        price_text = f"{car['price']:,}".replace(",", " ")

        if car["year"]:
            year_text = str(car["year"])
        else:
            year_text = "Məlum deyil"

        if car["km"]:
            km_text = f"{car['km']:,}".replace(",", " ") + " km"
        else:
            km_text = "Məlum deyil"

        message = (
            "🚗 TURBO.AZ AKTİV ELAN\n\n"
            f"📌 {car['title']}\n\n"
            f"💰 Qiymət: {price_text} AZN\n"
            f"📅 İl: {year_text}\n"
            f"🛣 Yürüş: {km_text}\n\n"
            f"🔗 {car['link']}\n\n"
            "✅ Elan səhifəsi açılır."
        )

        try:
            send_telegram(message)

        except Exception as error:
            print("Telegram xətası:", error)


if __name__ == "__main__":
    main()
