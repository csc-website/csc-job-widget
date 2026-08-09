import urllib.request
import xml.etree.ElementTree as ET


FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0 Safari/537.36"
)

TARGET_JOB = "22468412"


request = urllib.request.Request(
    FEED_URL,
    headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    },
)

print("Downloading CSC Career Center RSS feed...")

with urllib.request.urlopen(request, timeout=30) as response:
    xml_data = response.read()

print("RSS feed downloaded.")
print("Feed size:", len(xml_data), "bytes")

root = ET.fromstring(xml_data)

found = False

for item in root.iter():
    if not item.tag.lower().endswith("item"):
        continue

    item_xml = ET.tostring(
        item,
        encoding="unicode"
    )

    if TARGET_JOB in item_xml:
        found = True

        print("")
        print("=" * 80)
        print("FOUND TARGET JOB:", TARGET_JOB)
        print("=" * 80)
        print("")
        print(item_xml)
        print("")
        print("=" * 80)

        break

if not found:
    print("")
    print("TARGET JOB WAS NOT FOUND IN THE RSS FEED.")
    print("")
    print("The first few RSS items are shown below:")
    print("")

    count = 0

    for item in root.iter():
        if not item.tag.lower().endswith("item"):
            continue

        print(ET.tostring(item, encoding="unicode"))
        print("")
        print("-" * 80)

        count += 1

        if count >= 3:
            break
