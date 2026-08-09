import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape


FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"
MAX_JOBS = 10

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0 Safari/537.36"
)


def fetch(url, timeout=30):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def clean_text(text):
    if not text:
        return ""

    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


def make_job_page_url(link):
    if "/jobs/rss/" in link:
        return link.replace("/jobs/rss/", "/jobs/", 1)

    return link


def absolute_url(url, base_url):
    if not url:
        return ""

    url = unescape(url).strip()

    if url.startswith("//"):
        return "https:" + url

    return urllib.parse.urljoin(base_url, url)


def extract_image_from_rss(item, job_url):
    """
    Look for an image supplied directly inside the RSS item.
    """
    item_xml = ET.tostring(
        item,
        encoding="unicode"
    )

    patterns = [
        r'<[^>]+(?:media:content|media:thumbnail|enclosure)'
        r'[^>]+url=["\']([^"\']+)["\']',
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r'<img[^>]+src=([^ >]+)',
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            item_xml,
            re.IGNORECASE
        )

        if match:
            image_url = absolute_url(
                match.group(1).strip("\"'"),
                job_url
            )

            if image_url.startswith("http"):
                return image_url

    return ""


def extract_image_from_job_page(job_url):
    """
    Look for an Open Graph or Twitter image on the CSC Career Center
    job page.
    """
    try:
        html = fetch(job_url).decode(
            "utf-8",
            errors="replace"
        )
    except Exception as error:
        print(
            "Could not retrieve Career Center page for {}: {}".format(
                job_url,
                error
            )
        )
        return ""

    patterns = [
        r'<meta[^>]+property=["\']og:image["\']'
        r'[^>]+content=["\']([^"\']+)["\']',

        r'<meta[^>]+content=["\']([^"\']+)["\']'
        r'[^>]+property=["\']og:image["\']',

        r'<meta[^>]+name=["\']twitter:image["\']'
        r'[^>]+content=["\']([^"\']+)["\']',

        r'<meta[^>]+content=["\']([^"\']+)["\']'
        r'[^>]+name=["\']twitter:image["\']',
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            html,
            re.IGNORECASE
        )

        if match:
            image_url = absolute_url(
                match.group(1),
                job_url
            )

            if image_url.startswith("http"):
                return image_url

    return ""


def get_logo_url(item, job_url, employer):
    """
    Try to obtain a logo from the CSC Career Center itself.

    We deliberately do not search other websites. If the Career Center
    does not provide a logo, the job is still included normally.
    """

    logo_url = extract_image_from_rss(
        item,
        job_url
    )

    if logo_url:
        print(
            "Career Center logo for {}: {}".format(
                employer,
                logo_url
            )
        )
        return logo_url

    logo_url = extract_image_from_job_page(
        job_url
    )

    if logo_url:
        print(
            "Career Center page logo for {}: {}".format(
                employer,
                logo_url
            )
        )
        return logo_url

    print(
        "No Career Center logo found for {}".format(
            employer
        )
    )

    return ""


def main():
    print("Loading CSC Career Center RSS feed...")

    feed = fetch(FEED_URL)
    root = ET.fromstring(feed)

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
            parts = title.split("|", 1)

            title = parts[0].strip()
            employer = parts[1].strip()
        else:
            employer = ""

        job_page_url = make_job_page_url(
            link
        )

        print(
            "Checking Career Center page for {}:".format(
                employer
            )
        )

        print(job_page_url)

        logo_url = get_logo_url(
            item,
            job_page_url,
            employer
        )

        jobs.append(
            {
                "title": title,
                "employer": employer,
                "link": link,
                "company_logo_url": logo_url,
            }
        )

        if len(jobs) >= MAX_JOBS:
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


if __name__ == "__main__":
    main()
