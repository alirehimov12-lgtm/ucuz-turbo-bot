import requests

URL = "https://turbo.az/autos"

headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    response = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    print("STATUS:", response.status_code)
    print("FINAL URL:", response.url)
    print("LENGTH:", len(response.text))

    if response.status_code == 200:
        print("TURBO.AZ-A GIRIS VAR")
        
        # Konkret elan linklərini tap
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        links = []

        for a in soup.select("a.products-i__link"):
            href = a.get("href")

            if href:
                if href.startswith("/"):
                    href = "https://turbo.az" + href

                links.append(href)

        # Təkrarları sil
        links = list(dict.fromkeys(links))

        print("ELAN LINKLERI:", len(links))

        for link in links[:10]:
            print(link)

    else:
        print("TURBO.AZ GIRISI BLOKLADI")

except Exception as e:
    print("XETA:", e)
