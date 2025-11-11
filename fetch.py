# fetch.py
import requests


def fetch_html(url: str) -> str:
    url = url + "?printfull"

    # helps ensure we can get past the site blocks
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    r = requests.get(url, headers=headers)
    # checks for errors
    r.raise_for_status()
    # returns the string raw HTML source
    return r.text



if __name__ == "__main__":
    # tests the fetching of html
    user_url = input("Enter an AllRecipes URL: ")
    html = fetch_html(user_url)
    print("ld+json present?", "ld+json" in html)


