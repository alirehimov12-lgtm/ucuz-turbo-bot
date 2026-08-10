import os
import re
import statistics
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
SERPER_API_KEY = os.environ["SERPER_API_KEY"]

CHANNEL = "@ucuz_turboaz"

SERPER_URL = "https://google.serper.dev/search"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def serper_search(query):
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "q": query,
        "gl": "az",
        "hl": "az",
        "num": 10
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
        r'([\d\s.,]+)\s*₼',
        r'([\d\s.,]+)\s*AZN',
        r'qiyməti\s*([\d\s.,]+)',
        r'([\d\s.,]+)\s*manat'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            value = match.group(1)
            value = value.replace(" ", "").replace(",", ".")

            try:
                number = float(value)

                # Dollar/euro nəticələrini mümkün qədər keçirik
                if number > 0:
                    return number
            except:
                pass

    return None


def extract_year(text):
    if not text:
        return None

    years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)

    if years:
        year = int(years[0])

        if 1980 <= year <= 2026:
            return year

    return None


def extract_km(text):
    if not text:
        return None

    patterns = [
        r'([\d\s.,]+)\s*km',
        r'([\d\s.,]+)\s*KM'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            value = match.group(1)
            value = value.replace(" ", "").replace(".", "").replace(",", "")

            try:
                return int(value)
            except:
                pass

    return None


def get_cars(query):
    data = serper_search(query)

    cars = []

    for item in data.get("organic", []):
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")

        text = f"{title} {snippet}"

        # Yalnız Turbo.az nəticələri
        if "turbo.az" not in link:
            continue

        price = extract_price(text)
        year = extract_year(text)
        km = extract_km(text)

        if not price or not year:
            continue

        cars.append({
            "title": title,
            "snippet": snippet,
            "link": link,
            "price": price,
            "year": year,
            "km": km
        })

    return cars


def normalize_model(title):
    """
    Eyni marka/model üzrə sadə qruplaşdırma.
    """
    title = title.lower()

    # Turbo.az başlıqlarında marka/model adını mümkün qədər saxlayırıq
    title = re.sub(r'\s+', ' ', title)

    return title


def calculate_market_price(cars):
    """
    Tapılmış elanların qiymətlərindən bazar qiyməti çıxarır.
    Çox ucuz və çox baha nəticələrin təsirini azaltmaq üçün
    median istifadə olunur.
    """

    prices = [
        car["price"]
        for car in cars
        if car.get("price") and car["price"] > 500
    ]

    if len(prices) < 3:
        return None

    return statistics.median(prices)


def bargain_score(car, market_price):
    """
    Qiymət bazar qiymətindən nə qədər aşağıdır.
    """

    if not market_price:
        return 0

    difference = (market_price - car["price"]) / market_price * 100

    return round(difference, 1)


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

    # Turbo.az üzrə aktual elan axtarışları
    queries = [
        'site:turbo.az/autos Turbo.az avtomobil elanları 2026',
        'site:turbo.az/autos Turbo.az BMW Mercedes Toyota Kia Hyundai',
        'site:turbo.az/autos "₼" "km" "Bakı"'
    ]

    all_cars = []

    for query in queries:
        try:
            cars = get_cars(query)
            all_cars.extend(cars)
        except Exception as e:
            print("Search error:", e)

    # Eyni elanların təkrarını silirik
    unique = {}

    for car in all_cars:
        unique[car["link"]] = car

    cars = list(unique.values())

    if not cars:
        send_telegram(
            "🔎 Turbo.az axtarışında hazırda uyğun elan tapılmadı."
        )
        return

    # Ümumi bazar qiyməti
    market_price = calculate_market_price(cars)

    # Ən ucuz elanları seçirik
    scored = []

    for car in cars:
        score = bargain_score(car, market_price)

        car["score"] = score

        if score >= 15:
            scored.append(car)

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Maksimum 5 elan göndər
    scored = scored[:5]

    if not scored:
        send_telegram(
            "🔎 Turbo.az-da elanlar tapıldı, amma "
            "bazar qiymətindən ən azı 15% ucuz görünən elan yoxdur."
        )
        return

    for car in scored:

        price_text = f"{car['price']:,.0f} ₼".replace(",", " ")

        if car["km"]:
            km_text = f"{car['km']:,} km".replace(",", " ")
        else:
            km_text = "Yürüş məlum deyil"

        message = (
            "🚨 UCUZ ELAN TAPILDI\n\n"
            f"🚗 {car['title']}\n"
            f"💰 Qiymət: {price_text}\n"
            f"📅 İl: {car['year']}\n"
            f"🛣 Yürüş: {km_text}\n\n"
            f"📊 Bazar qiymətindən təxminən: "
            f"{car['score']}% aşağı\n\n"
            f"🔗 {car['link']}\n\n"
            "⚠️ Qiymətləndirmə yalnız elan məlumatlarına "
            "əsaslanan ilkin analizdir."
        )

        try:
            send_telegram(message)
        except Exception as e:
            print("Telegram error:", e)


if __name__ == "__main__":
    main()
