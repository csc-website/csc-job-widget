import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"
OUTPUT = Path("jobs.json")
LIMIT = 5

USER_AGENT = "CSC-Job-Widget/1.0"

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

def split_title_employer(title):
    """
    CSC's RSS feed puts the employer after a | character.
    Example:
    Director of Communications | University of Oklahoma Athletics
    """
    if "|" in title:
        job_title, employer = title.split("|", 1)
        return job_title.strip(), employer.strip()

    return title.strip(), ""

def main():
    request = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": USER_AGENT}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)

    jobs = []

    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1].lower() != "item":
            continue

        raw_title = first_text(item, {"title"})
        link = first_text(item, {"link", "guid"})

        if not raw_title or not link:
            continue

        title, employer = split_title_employer(raw_title)

        if link.startswith("/"):
            link = "https://careercenter.collegesportscommunicators.com" + link

        jobs.append({
            "title": title,
            "employer": employer,
            "link": link
        })

        if len(jobs) >= LIMIT:
            break

    if not jobs:
        raise RuntimeError("No usable jobs were found in the RSS feed.")

    OUTPUT.write_text(
        json.dumps(jobs, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

if __name__ == "__main__":
    main()
