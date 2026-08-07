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

request = urllib.request.Request(
    FEED_URL,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    xml = response.read()

root = ET.fromstring(xml)

jobs = []

for item in root.iter():
    if item.tag.lower().endswith("item"):

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

        # CSC places the employer after a | character.
        if "|" in title:
            title, employer = title.split("|", 1)
            title = title.strip()
            employer = employer.strip()
        else:
            employer = ""

        jobs.append({
            "title": title,
            "employer": employer,
            "link": link
        })

        if len(jobs) == 5:
            break

with open("jobs.json", "w", encoding="utf-8") as file:
    json.dump(jobs, file, indent=2, ensure_ascii=False)

print(f"Updated {len(jobs)} jobs.")
