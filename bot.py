import os
import re
import statistics
import requests
from urllib.parse import quote

BOT_TOKEN = os.environ["BOT_TOKEN"]
SERPER_API_KEY = os.environ["SERPER_API_KEY"]

CHANNEL = "@ucuz_turboaz"

SERPER_URL = "https://google.serper.dev/search"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

MAX_PRICE = 30000
MIN_DISCOUNT = 20
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

    r = requests.post(
        SERPER_URL,
        headers=headers,
        json=data,
        timeout=30
    )

    r.raise_for_status()
    return r.json()


def extract_price(text):
    patterns = [
        r'(\d{1,3}(?:[ .]\d{3})+)\s*(?:AZN|₼|manat)',
        r'(\d{4,6})\s*(?:AZN|₼|manat)'
    ]

    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)

        if m:
            value = m.group(1)
            value = value.replace(" ", "").replace(".", "")

            try:
                price = int(value)

                if 500 <= price <= MAX_PRICE:
                    return price
            except ValueError:
                pass

    return None


def extract_year(text):
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)

    for y in years:
        year = int(y)

        if 1980 <= year <= 2026:
            return year

    return None


def extract_km(text):
    patterns = [
        r'([\d .]+)\s*km',
        r'([\d .]+)\s*KM'
    ]

    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)

        if m:
            value = m.group(1)
            value = value.replace(" ", "").replace(".", "")

            try:
                return int(value)
            except ValueError:
                pass

    return None


def is_active(url):
    """
    Turbo.az elan səhifəsinin hələ mövcud olub-olmadığını yoxlayır.
    Səhifə silinibsə / artıq mövcud deyilsə False qaytarır.
    """

    try:
        r = session.get(
            url,
            timeout=15,
            allow_redirects=True
        )

        if r.status_code != 200:
            return False

        text = r.text.lower()

        inactive_words = [
            "elan tapılmadı",
            "elan mövcud deyil",
            "elan silinib",
            "page not found",
            "not found"
        ]

        for word in inactive_words:
            if word in text:
                return False

        return "turbo.az" in r.url.lower()

    except Exception as e:
        print("Aktivlik yoxlaması:", e)
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

        if not price:
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


def market_price(cars):
    prices = [
        c["price"]
        for c in cars
        if 500 <= c["price"] <= MAX_PRICE
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

    r = requests.post(
        TELEGRAM_URL,
        data=data,
        timeout=30
    )

    r.raise_for_status()


def main():

    queries = [
        'site:turbo.az/autos/ "AZN" "km"',
        'site:turbo.az/autos/ "₼" "km"',
        'site:turbo.az/autos/ "manat" "km"',
        'site:turbo.az/autos/ 2026 avtomobil',
        'site:turbo.az/autos/ 2025 avtomobil'
    ]

    all_cars = []

    for query in queries:

        try:
            cars = get_cars(query)
            all_cars.extend(cars)

        except Exception as e:
            print("Google axtarış xətası:", e)

    # Təkrar elanları sil
    unique = {}

    for car in all_cars:
        unique[car["link"]] = car

    cars = list(unique.values())

    print("Tapılan elan:", len(cars))

    if not cars:
        send_telegram(
            "🔎 30 000 AZN-ə qədər uyğun Turbo.az elanı tapılmadı."
        )
        return

    # Aktiv elanları yoxla
    active_cars = []

    for car in cars:

        print("Yoxlanılır:", car["link"])

        if is_active(car["link"]):
            active_cars.append(car)

    print("Aktiv elan:", len(active_cars))

    if not active_cars:
        send_telegram(
            "🔎 Aktiv Turbo.az elanı tapılmadı."
        )
        return

    # Bazar qiyməti
    market = market_price(active_cars)

    if not market:
        send_telegram(
            "📊 Aktiv elanlar tapıldı, amma "
            "bazar qiymətini hesablamaq üçün kifayət qədər "
            "oxşar qiymət yoxdur."
        )
        return

    print("Bazar medianı:", market)

    good_deals = []

    for car in active_cars:

        discount = (
            (market - car["price"]) /
            market
        ) * 100

        car["discount"] = round(discount, 1)

        if discount >= MIN_DISCOUNT:
            good_deals.append(car)

    good_deals.sort(
        key=lambda x: x["discount"],
        reverse=True
    )

    # Maksimum 10 ən yaxşı elan
    good_deals = good_deals[:10]

    if not good_deals:

        send_telegram(
            f"🔎 30 000 AZN-ə qədər aktiv elanlar tapıldı.\n\n"
            f"📊 Cari bazar medianı: {market:,.0f} AZN\n\n"
            f"🔥 Amma bazardan ən azı {MIN_DISCOUNT}% "
            f"ucuz elan tapılmadı."
        )

        return

    for car in good_deals:

        price = f"{car['price']:,}".replace(",", " ")
        market_text = f"{market:,.0f}".replace(",", " ")

        if car["km"]:
            km = f"{car['km']:,}".replace(",", " ") + " km"
        else:
            km = "Məlum deyil"

        year = car["year"] if car["year"] else "Məlum deyil"

        if car["discount"] >= 30:
            badge = "🔥🔥 ÇOX UCUZ"
        else:
            badge = "🔥 YAXŞI FÜRSƏT"

        message = (
            f"{badge}\n\n"
            f"🚗 {car['title']}\n\n"
            f"💰 Elan qiyməti: {price} AZN\n"
            f"📊 Təxmini bazar qiyməti: {market_text} AZN\n"
            f"📉 Fərq: {car['discount']}%\n"
            f"📅 İl: {year}\n"
            f"🛣 Yürüş: {km}\n\n"
            f"🔗 {car['link']}\n\n"
            f"✅ Elan aktiv olaraq yoxlanılıb.\n"
            f"⚠️ Qiymətləndirmə ilkin avtomatik analizdir."
        )

        try:
            send_telegram(message)

        except Exception as e:
            print("Telegram xətası:", e)


if __name__ == "__main__":
    main()
