import json
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
import re
from urllib.parse import quote_plus

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"

# Known employers are used first. New employers can be handled by the
# automatic logo service below without editing this file.
KNOWN_DOMAINS = {
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

def clean_text(text):
    if not text:
        return ""

    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())

def find_domain_from_search(employer):
    query = quote_plus('"' + employer + '" official website')

    url = (
        "https://www.google.com/search?q="
        + query
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    try:
        response = urllib.request.urlopen(
            request,
            timeout=15
        )

        html = response.read().decode(
            "utf-8",
            errors="replace"
        )

        response.close()

    except Exception as error:
        print(
            "Automatic domain search failed for {}: {}".format(
                employer,
                error
            )
        )
        return ""

    # Look for normal external HTTPS links in search results.
    links = re.findall(
        r'https?://[^"\'<>\s&]+',
        html,
        re.IGNORECASE
    )

    ignored_domains = {
        "google.com",
        "www.google.com",
        "accounts.google.com",
        "support.google.com",
        "policies.google.com",
        "youtube.com",
        "www.youtube.com",
        "facebook.com",
        "www.facebook.com",
        "instagram.com",
        "www.instagram.com",
        "linkedin.com",
        "www.linkedin.com",
        "twitter.com",
        "x.com",
        "www.x.com"
    }

    for link in links:
        link = link.replace(
            "\\u0026",
            "&"
        )

        match = re.match(
            r"https?://(?:www\.)?([^/]+)",
            link,
            re.IGNORECASE
        )

        if not match:
            continue

        domain = match.group(1).lower()

        if domain in ignored_domains:
            continue

        if domain.endswith(".google.com"):
            continue

        return domain

    return ""

def get_logo_url(employer):
    domain = KNOWN_DOMAINS.get(employer)

    if not domain:
        domain = find_domain_from_search(employer)

    if not domain:
        print(
            "No official domain found for {}".format(
                employer
            )
        )
        return ""

    logo_url = (
        "https://www.google.com/s2/favicons"
        "?domain="
        + quote_plus(domain)
        + "&sz=128"
    )

    print(
        "Logo domain for {}: {}".format(
            employer,
            domain
        )
    )

    return logo_url

request = urllib.request.Request(
    FEED_URL,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

response = urllib.request.urlopen(
    request,
    timeout=30
)

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

    title = clean_text(title)
    link = unescape(link).strip()

    if not title or not link:
        continue

    if "|" in title:

        parts = title.split(
            "|",
            1
        )

        title = parts[0].strip()
        employer = parts[1].strip()

    else:

        employer = ""

    logo_url = get_logo_url(
        employer
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
