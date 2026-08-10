import os
import requests

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


def check_deal(car_name, price, market_price):
    difference = market_price - price
    percent = (difference / market_price) * 100

    if percent >= 20:
        message = (
            f"🔥 BAZARDAN {percent:.0f}% UCUZ\n\n"
            f"🚗 {car_name}\n"
            f"💰 Elan qiyməti: {price:,.0f} AZN\n"
            f"📊 Bazar qiyməti: {market_price:,.0f} AZN\n"
            f"📉 Fərq: {difference:,.0f} AZN"
        )

        send_message(message)


if __name__ == "__main__":

    # TEST
    check_deal(
        car_name="BMW 520i 2015",
        price=24000,
        market_price=30000
    )
