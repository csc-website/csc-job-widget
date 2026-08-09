import json
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
import re

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"

def clean(text):
    if not text:
        return ""

    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)

    return " ".join(text.split())

def fetch_url(url):
request = urllib.request.Request(
url,
headers={
"User-Agent": "Mozilla/5.0",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
"Accept-Language": "en-US,en;q=0.9",
},
)

with urllib.request.urlopen(request, timeout=30) as response:
    return response.read().decode("utf-8", errors="replace")

def extract_logo_url(html):
patterns = [
"""<meta[^>]+property=["']og:image[^>]+content=["']([^%22']+)["']""",
"""<meta[^>]+content=["']([^%22']+)["'][^>]+property=["']og:image""",
"""<meta[^>]+name=["']twitter:image[^>]+content=["']([^%22']+)["']""",
"""<meta[^>]+content=["']([^%22']+)["'][^>]+name=["']twitter:image""",
]

for pattern in patterns:
    match = re.search(pattern, html, re.IGNORECASE)

    if match:
        logo_url = unescape(match.group(1).strip())

        if logo_url.startswith("//"):
            logo_url = "https:" + logo_url

        return logo_url

return ""

# Download RSS feed

request = urllib.request.Request(
FEED_URL,
headers={
"User-Agent": "Mozilla/5.0",
"Accept": "application/rss+xml, application/xml, text/xml, */*",
},
)

with urllib.request.urlopen(request, timeout=30) as response:
xml = response.read()

root = ET.fromstring(xml)

jobs = []

# Process RSS jobs

for item in root.iter():

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


# Separate job title and employer

if "|" in title:

    title, employer = title.split("|", 1)

    title = title.strip()
    employer = employer.strip()

else:

    employer = ""


# Convert RSS URL to normal job URL

job_page_url = link.replace(
    "/jobs/rss/",
    "/jobs/",
    1
)


print("")
print("Checking normal Career Center page for {}:".format(employer))
print(job_page_url)


logo_url = ""


# Retrieve normal job page

try:

    page_html = fetch_url(job_page_url)

    logo_url = extract_logo_url(page_html)


    if logo_url:

        print(
            "Career Center logo found for {}: {}".format(
                employer,
                logo_url
            )
        )

    elif "showLogo.cfm" in page_html:

        print(
            "showLogo.cfm found for {}, but the logo URL "
            "could not be extracted.".format(
                employer
            )
        )

    elif (
        "captcha" in page_html.lower()
        or "bot check" in page_html.lower()
        or "checking your browser" in page_html.lower()
        or "javascript required" in page_html.lower()
    ):

        print(
            "Career Center returned a bot/challenge page "
            "for {}".format(
                employer
            )
        )

    else:

        print(
            "No Career Center logo found for {}".format(
                employer
            )
        )


except Exception as error:

    print(
        "Could not retrieve Career Center page for {}: {}".format(
            employer,
            error
        )
    )


# Add job

jobs.append(
    {
        "title": title,
        "employer": employer,
        "link": link,
        "company_logo_url": logo_url
    }
)


# Keep the existing 10-job limit

if len(jobs) >= 10:
    break

# Write jobs.json

with open(
"jobs.json",
"w",
encoding="utf-8"
) as file:

json.dump(
    jobs,
    file,
    indent=2,
    ensure_ascii=False
)

print("")
print(
"Updated {} jobs.".format(
len(jobs)
)
)
