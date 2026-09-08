import urllib.request
import xml.etree.ElementTree as ET

url = "https://blog.google/technology/ai/rss/"

try:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read()

    root = ET.fromstring(data)

    print("\n🌐 AI KHOJ RSS TEST")
    print("=" * 40)

    count = 0

    for item in root.iter("item"):
        title = item.findtext("title")

        if title:
            count += 1
            print(f"{count}. {title}")

        if count >= 5:
            break

    if count == 0:
        print("❌ कोई RSS item नहीं मिला")

except Exception as e:
    print("❌ Error:", e)
