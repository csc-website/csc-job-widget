import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"
OUTPUT = Path("jobs.json")
LIMIT = 5

USER_AGENT = "CSC-Job-Widget/1.0 (+https://github.com/csc-website/csc-job-widget)"

def clean(value):
    if value is None:
        return ""
    value = unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"\s+", " ", value).strip()

def first_text(item, names):
    for child in list(item):
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag in names:
            value = clean(child.text)
            if value:
                return value
    return ""

def extract_employer(item):
    # Prefer explicit employer/company fields if the feed provides one.
    employer = first_text(item, {"employer", "company", "organization", "organizationname"})
    if employer:
        return employer

    # Common RSS feeds expose the employer as author/creator.
    employer = first_text(item, {"author", "creator"})
    if employer and "@" not in employer:
        return employer

    # Fall back to the first non-empty line of the description.
    description = first_text(item, {"description", "summary", "content"})
    if description:
        parts = [p.strip() for p in re.split(r"[\r\n|]+", description) if p.strip()]
        if parts:
            candidate = parts[0]
            if len(candidate) <= 150 and candidate.lower() not in {"job description", "description"}:
                return candidate

    return ""

def main():
    request = urllib.request.Request(FEED_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = []

    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1].lower() != "item":
            continue

        title = first_text(item, {"title"})
        link = first_text(item, {"link", "guid"})
        employer = extract_employer(item)

        if not title or not link:
            continue

        if link.startswith("/"):
            link = "https://careercenter.collegesportscommunicators.com" + link

        items.append({
            "title": title,
            "employer": employer,
            "link": link
        })

        if len(items) >= LIMIT:
            break

    if not items:
        raise RuntimeError("The RSS feed returned no usable job items.")

    OUTPUT.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
