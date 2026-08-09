import json
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
import re
from urllib.parse import quote

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"

# The Career Center blocks automated requests to individual job pages.
# We therefore use stable official institutional domains for logos instead.
EMPLOYER_DOMAINS = {
    "Ferris State University": "ferris.edu",
    "University of Oklahoma Athletics": "soonersports.com",
    "University of Utah": "utah.edu",
    "University of Illinois Chicago": "uic.edu",
    "Keiser University": "keiseruniversity.edu",
    "Wichita State Athletics": "goshockers.com",
    "Queens University of Charlotte": "queens.edu",
    "University of Kentucky Athletics": "ukathletics.com",
    "Penn State Athletics": "gopsusports.com",
    "Weber State University": "weber.edu"
}

def get_logo_url(employer):
    domain = EMPLOYER_DOMAINS.get(employer)

    if not domain:
        return ""

    return (
        "https://www.google.com/s2/favicons"
        "?domain=" + quote(domain)
        + "&sz=128"
    )

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

    logo_url = get_logo_url(employer)

    if logo_url:
        print(
            "Using official-domain logo for {}: {}".format(
                employer,
                logo_url
            )
        )
    else:
        print(
            "No logo mapping for {}".format(
                employer
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

print(
    "Updated {} jobs.".format(
        len(jobs)
    )
)
