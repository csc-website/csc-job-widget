import json
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
import re

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"

request = urllib.request.Request(
FEED_URL,
headers={"User-Agent": "Mozilla/5.0"}
)

response = urllib.request.urlopen(request, timeout=30)
xml = response.read()
response.close()

root = ET.fromstring(xml)

jobs = []

for item in root.iter():

```
if not item.tag.lower().endswith("item"):
    continue

title = ""
link = ""

for child in item:

    tag = child.tag.lower()

    if tag.endswith("title"):
        title = child.text or ""

    elif tag.endswith("link"):
        link = child.text or ""

title = unescape(title)
title = re.sub(r"<[^>]+>", "", title)
title = " ".join(title.split())
link = unescape(link).strip()

if not title or not link:
    continue

if "|" in title:

    parts = title.split("|", 1)
    title = parts[0].strip()
    employer = parts[1].strip()

else:

    employer = ""

job_page_url = link.replace(
    "/jobs/rss/",
    "/jobs/",
    1
)

logo_url = ""

try:

    page_request = urllib.request.Request(
        job_page_url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    page_response = urllib.request.urlopen(
        page_request,
        timeout=30
    )

    page_html = page_response.read().decode(
        "utf-8",
        errors="replace"
    )

    page_response.close()

    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']'
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            page_html,
            re.IGNORECASE
        )

        if match:

            logo_url = unescape(
                match.group(1).strip()
            )

            break

    if logo_url:

        print(
            "Found logo for {}: {}".format(
                employer,
                logo_url
            )
        )

    else:

        print(
            "No logo found for {}".format(
                employer
            )
        )

except Exception as error:

    print(
        "Could not retrieve logo for {}: {}".format(
            employer,
            error
        )
    )

jobs.append(
    {
        "title": title,
        "employer": employer,
        "link": link,
        "company_logo_url": logo_url
    }
)

if len(jobs) >= 10:
    break
```

file = open(
"jobs.json",
"w",
encoding="utf-8"
)

json.dump(
jobs,
file,
indent=2,
ensure_ascii=False
)

file.close()

print(
"Updated {} jobs.".format(
len(jobs)
)
)
