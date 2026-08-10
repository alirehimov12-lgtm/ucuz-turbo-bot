import os
import requests
from statistics import median

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@ucuz_turboaz"


def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHANNEL,
            "text": text
        },
        timeout=20
    )

    print(response.status_code)
    print(response.text)


def calculate_market_price(similar_cars):
    """
    similar_cars:
    [
        {"year": 2015, "mileage": 170000, "price": 29500},
        {"year": 2015, "mileage": 190000, "price": 28000},
        ...
    ]

    Median qiymət istifadə olunur.
    Bu, həddindən artıq baha və ya ucuz elanların
    nəticəni pozmasının qarşısını alır.
    """

    prices = [
        car["price"]
        for car in similar_cars
        if car.get("price", 0) > 0
    ]

    if len(prices) < 3:
        return None

    return median(prices)


def is_similar(car, candidate):
    """
    Analogi elan seçmək üçün əsas meyarlar.
    """

    # Eyni marka/model
    if car["make"].lower() != candidate["make"].lower():
        return False

    if car["model"].lower() != candidate["model"].lower():
        return False

    # İl maksimum +/- 1 il
    if abs(car["year"] - candidate["year"]) > 1:
        return False

    # Yürüş maksimum +/- 50 000 km
    if abs(car["mileage"] - candidate["mileage"]) > 50000:
        return False

    # Mühərrik həcmi
    if car.get("engine") and candidate.get("engine"):
        if abs(car["engine"] - candidate["engine"]) > 0.2:
            return False

    # Karobka
    if car.get("gearbox") and candidate.get("gearbox"):
        if car["gearbox"].lower() != candidate["gearbox"].lower():
            return False

    return True


def analyze_car(car, all_cars):

    similar_cars = [
        candidate
        for candidate in all_cars
        if candidate is not car
        and is_similar(car, candidate)
    ]

    # Ən azı 5 analoji elan tələb edirik
    if len(similar_cars) < 5:
        print(
            f"{car['make']} {car['model']} üçün "
            f"kifayət qədər analoji elan yoxdur."
        )
        return

    market_price = calculate_market_price(similar_cars)

    if not market_price:
        return

    difference = market_price - car["price"]
    percent = (difference / market_price) * 100

    print(
        f"{car['make']} {car['model']} | "
        f"Elan: {car['price']} | "
        f"Bazar: {market_price:.0f} | "
        f"Fərq: {percent:.1f}%"
    )

    # Yalnız 20% və daha çox ucuz elanlar
    if percent >= 20:

        message = (
            f"🔥 BAZARDAN {percent:.0f}% UCUZ\n\n"
            f"🚗 {car['make']} {car['model']}\n"
            f"📅 İl: {car['year']}\n"
            f"🛣 Yürüş: {car['mileage']:,} km\n"
            f"⚙️ Mühərrik: {car.get('engine', '—')} L\n"
            f"🔧 Karobka: {car.get('gearbox', '—')}\n\n"
            f"💰 Elan: {car['price']:,.0f} AZN\n"
            f"📊 Bazar: {market_price:,.0f} AZN\n"
            f"📉 Fərq: {difference:,.0f} AZN\n\n"
            f"🔗 {car.get('url', 'Link yoxdur')}"
        )

        send_message(message)


if __name__ == "__main__":

    # TEST MƏLUMATLARI
    cars = [
        {
            "make": "BMW",
            "model": "520i",
            "year": 2015,
            "mileage": 170000,
            "engine": 2.0,
            "gearbox": "avtomat",
            "price": 22500,
            "url": "https://turbo.az/"
        },
        {
            "make": "BMW",
            "model": "520i",
            "year": 2015,
            "mileage": 180000,
            "engine": 2.0,
            "gearbox": "avtomat",
            "price": 29500
        },
        {
            "make": "BMW",
            "model": "520i",
            "year": 2015,
            "mileage": 165000,
            "engine": 2.0,
            "gearbox": "avtomat",
            "price": 30000
        },
        {
            "make": "BMW",
            "model": "520i",
            "year": 2016,
            "mileage": 175000,
            "engine": 2.0,
            "gearbox": "avtomat",
            "price": 31000
        },
        {
            "make": "BMW",
            "model": "520i",
            "year": 2015,
            "mileage": 200000,
            "engine": 2.0,
            "gearbox": "avtomat",
            "price": 28500
        },
        {
            "make": "BMW",
            "model": "520i",
            "year": 2014,
            "mileage": 160000,
            "engine": 2.0,
            "gearbox": "avtomat",
            "price": 29000
        }
    ]

    # Bütün elanları yoxla
    for car in cars:
        analyze_car(car, cars)
