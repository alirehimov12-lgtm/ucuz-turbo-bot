import requests
from bs4 import BeautifulSoup
import re

GOOGLE_URL = "https://www.google.com/search"

QUERIES = [
    "Turbo.az BMW",
    "Turbo.az Mercedes",
    "Turbo.az Toyota",
    "Turbo.az Kia",
    "Turbo.az Hyundai",
    "Turbo.az Volkswagen",
    "Turbo.az Nissan",
    "Turbo.az Lexus",
    "Turbo.az Audi",
    "Turbo.az Honda"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "az-AZ,az;q=0.9,en;q=0.8"
}


def search_google(query):
    try:
        response = requests.get(
            GOOGLE_URL,
            params={
                "q": query,
                "hl": "az",
                "num": 30
            },
            headers=HEADERS,
            timeout=30
        )

        print("GOOGLE STATUS:", response.status_code)

        if response.status_code != 200:
            print(response.text[:1000])
            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        for a in soup.find_all("a", href=True):

            link = a.get("href", "")

            # Yalnız konkret Turbo.az elanları
            if re.search(
                r"https?://turbo\.az/autos/\d+",
                link
            ):

                title = a.get_text(
                    " ",
                    strip=True
                )

                results.append({
                    "title": title,
                    "link": link
                })

        return results

    except Exception as error:

        print(
            "GOOGLE ERROR:",
            error
        )

        return []


def main():

    all_results = {}

    for query in QUERIES:

        print()
        print("SEARCH:", query)

        results = search_google(query)

        print(
            "CONCRETE RESULTS:",
            len(results)
        )

        for result in results:

            link = result["link"]

            all_results[link] = result

    print()
    print(
        "TOTAL CONCRETE TURBO.AZ ADS:",
        len(all_results)
    )

    print()

    for number, item in enumerate(
        list(all_results.values())[:30],
        1
    ):

        print(
            number,
            item["title"]
        )

        print(
            item["link"]
        )

        print()


if __name__ == "__main__":
    main()
