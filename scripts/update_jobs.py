import json
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
import re

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"

# Get the RSS feed

request = urllib.request.Request(
FEED_URL,
headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
xml = response.read()

root = ET.fromstring(xml)

jobs = []

# Process each job in the RSS feed

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

# Clean the title and link
title = unescape(title)
title = re.sub(r"<[^>]+>", "", title)
title = " ".join(title.split())
link = unescape(link).strip()

if not title or not link:
    continue

# The RSS title is formatted:
# Job Title | Employer
if "|" in title:

    title, employer = title.split("|", 1)

    title = title.strip()
    employer = employer.strip()

else:

    employer = ""

# Convert the RSS job URL:
#
# /jobs/rss/22468412/job-title
#
# to the normal job page:
#
# /jobs/22468412/job-title
job_page_url = link.replace(
    "/jobs/rss/",
    "/jobs/",
    1
)

logo_url = ""

try:

    # Request the normal job page.
    page_request = urllib.request.Request(
        job_page_url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        page_request,
        timeout=30
    ) as page_response:

        page_html = page_response.read().decode(
            "utf-8",
            errors="replace"
        )

    # Look for the Open Graph logo.
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

# Add the job
jobs.append(
    {
        "title": title,
        "employer": employer,
        "link": link,
        "company_logo_url": logo_url
    }
)

# Keep the widget limited to 10 jobs.
if len(jobs) >= 10:
    break
```

# Write the updated jobs file.

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
"Updated {} jobs.".format(
len(jobs)
)
)
