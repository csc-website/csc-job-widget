import json
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
import re

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"

def clean(text):
if not text:
return ""

```
text = unescape(text)
text = re.sub(r"<[^>]+>", "", text)

return " ".join(text.split())
```

def fetch_url(url):
request = urllib.request.Request(
url,
headers={
"User-Agent": "Mozilla/5.0"
}
)

```
with urllib.request.urlopen(request, timeout=30) as response:
    return response.read().decode("utf-8", errors="replace")
```

def get_job_page_url(rss_url):
"""
Convert the RSS job URL to the normal job-page URL.
"""

```
return rss_url.replace(
    "/jobs/rss/",
    "/jobs/",
    1
)
```

def extract_logo(html):
"""
Look for the company's logo in the job page's
Open Graph metadata.
"""

```
patterns = [
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
]

for pattern in patterns:
    match = re.search(
        pattern,
        html,
        re.IGNORECASE
    )

    if match:
        logo_url = unescape(
            match.group(1).strip()
        )

        if logo_url.startswith("//"):
            logo_url = "https:" + logo_url

        return logo_url

return ""
```

request = urllib.request.Request(
FEED_URL,
headers={
"User-Agent": "Mozilla/5.0"
}
)

with urllib.request.urlopen(
request,
timeout=30
) as response:

```
xml = response.read()
```

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
        title = clean(child.text)

    elif tag.endswith("link"):
        link = clean(child.text)

if not title or not link:
    continue


if "|" in title:

    title, employer = title.split(
        "|",
        1
    )

    title = title.strip()
    employer = employer.strip()

else:

    employer = ""


job_page_url = get_job_page_url(link)

logo_url = ""


try:

    page_html = fetch_url(
        job_page_url
    )

    logo_url = extract_logo(
        page_html
    )

    if logo_url:

        print(
            f"Found logo for {employer}: {logo_url}"
        )

    else:

        print(
            f"No logo found for {employer}"
        )

except Exception as error:

    print(
        f"Could not retrieve logo for {title}: {error}"
    )


job = {
    "title": title,
    "employer": employer,
    "link": link,
    "company_logo_url": logo_url
}

jobs.append(job)


if len(jobs) == 10:
    break
```

with open(
"jobs.json",
"w",
encoding="utf-8"
) as file:

```
json.dump(
    jobs,
    file,
    indent=2,
    ensure_ascii=False
)
```

print(
f"Updated {len(jobs)} jobs."
)
