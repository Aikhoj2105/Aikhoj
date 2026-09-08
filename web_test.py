import urllib.request
import urllib.parse
import re

query = input("🔎 Search: ")

url = "https://www.google.com/search?" + urllib.parse.urlencode({
    "q": query
})

request = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

try:
    with urllib.request.urlopen(request) as response:
        html = response.read().decode("utf-8", errors="ignore")

    # Basic title extraction
    titles = re.findall(r"<h3[^>]*>(.*?)</h3>", html)

    print("\n🌐 SEARCH RESULTS")
    print("=" * 40)

    if titles:
        for i, title in enumerate(titles[:5], 1):
            title = re.sub("<.*?>", "", title)
            print(f"{i}. {title}")
    else:
        print("❌ Results नहीं मिले")

except Exception as e:
    print("❌ Error:", e)
