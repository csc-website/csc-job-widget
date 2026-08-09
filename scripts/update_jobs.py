import json
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
import re
from urllib.parse import quote_plus, urljoin, urlparse

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"

def clean_text(text):
    if not text:
        return ""

    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())

def get_html(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/151.0 Safari/537.36"
            )
        }
    )

    response = urllib.request.urlopen(
        request,
        timeout=20
    )

    html = response.read().decode(
        "utf-8",
        errors="replace"
    )

    response.close()

    return html

def search_athletics_domain(employer):
    query = quote_plus(
        '"' + employer + '" athletics official website'
    )

    search_url = (
        "https://www.google.com/search?q="
        + query
    )

    try:
        html = get_html(search_url)
    except Exception as error:
        print(
            "Athletics-domain search failed for {}: {}".format(
                employer,
                error
            )
        )
        return ""

    links = re.findall(
        r'https?://[^"\'<>\s&]+',
        html,
        re.IGNORECASE
    )

    ignored = {
        "google.com",
        "www.google.com",
        "accounts.google.com",
        "support.google.com",
        "facebook.com",
        "www.facebook.com",
        "instagram.com",
        "www.instagram.com",
        "linkedin.com",
        "www.linkedin.com",
        "twitter.com",
        "x.com",
        "www.x.com",
        "youtube.com",
        "www.youtube.com",
        "wikipedia.org",
        "www.wikipedia.org"
    }

    candidates = []

    for link in links:
        match = re.match(
            r"https?://(?:www\.)?([^/]+)",
            link,
            re.IGNORECASE
        )

        if not match:
            continue

        domain = match.group(1).lower()

        if domain in ignored:
            continue

        if domain.endswith(".google.com"):
            continue

        score = 0

        if "athletic" in domain:
            score += 10

        if "sports" in domain:
            score += 10

        if "sooner" in domain:
            score += 5

        if "utes" in domain:
            score += 5

        if "wildcat" in domain:
            score += 5

        if "cardinal" in domain:
            score += 5

        if "bulldog" in domain:
            score += 5

        if "tiger" in domain:
            score += 5

        if "eagle" in domain:
            score += 5

        if "bear" in domain:
            score += 5

        if "knight" in domain:
            score += 5

        if "hawk" in domain:
            score += 5

        if "panther" in domain:
            score += 5

        if "university" in domain:
            score += 2

        candidates.append(
            (score, domain)
        )

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # Try the strongest candidates first and verify that the site
    # actually contains athletics-related content.
    tried = set()

    for score, domain in candidates:

        if domain in tried:
            continue

        tried.add(domain)

        if score < 2:
            continue

        site_url = "https://" + domain + "/"

        try:
            html = get_html(site_url)
        except Exception:
            continue

        lower_html = html.lower()

        athletics_terms = [
            "athletics",
            "sports",
            "varsity",
            "ncaa",
            "roster",
            "schedule",
            "scoreboard"
        ]

        matches = sum(
            1
            for term in athletics_terms
            if term in lower_html
        )

        if matches >= 2:
            print(
                "Athletics site for {}: {}".format(
                    employer,
                    site_url
                )
            )
            return site_url

    return ""

def find_logo_on_athletics_site(site_url):
    try:
        html = get_html(site_url)
    except Exception as error:
        print(
            "Could not retrieve athletics site {}: {}".format(
                site_url,
                error
            )
        )
        return ""

    # Prefer an actual image whose filename, alt text, class, or id
    # identifies it as the site's logo.
    image_patterns = [
        r'<img[^>]+(?:class|id)=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
        r'<img[^>]+src=["\']([^"\']*logo[^"\']*)["\'][^>]*>',
        r'<img[^>]+alt=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]+alt=["\'][^"\']*logo[^"\']*["\']'
    ]

    for pattern in image_patterns:

        match = re.search(
            pattern,
            html,
            re.IGNORECASE
        )

        if match:

            logo_url = urljoin(
                site_url,
                unescape(match.group(1).strip())
            )

            if logo_url.startswith("http"):
                print(
                    "Athletics logo found: {}".format(
                        logo_url
                    )
                )
                return logo_url

    # Next try Open Graph and Twitter images.
    meta_patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']'
    ]

    for pattern in meta_patterns:

        match = re.search(
            pattern,
            html,
            re.IGNORECASE
        )

        if match:

            image_url = urljoin(
                site_url,
                unescape(match.group(1).strip())
            )

            if image_url.startswith("http"):
                print(
                    "Athletics site image found: {}".format(
                        image_url
                    )
                )
                return image_url

    # Finally use the site's icon as a last resort.
    icon_patterns = [
        r'<link[^>]+rel=["\'][^"\']*(?:icon|apple-touch-icon)[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\'][^"\']*(?:icon|apple-touch-icon)[^"\']*["\']'
    ]

    for pattern in icon_patterns:

        match = re.search(
            pattern,
            html,
            re.IGNORECASE
        )

        if match:

            icon_url = urljoin(
                site_url,
                unescape(match.group(1).strip())
            )

            if icon_url.startswith("http"):
                print(
                    "Athletics site icon found: {}".format(
                        icon_url
                    )
                )
                return icon_url

    return ""

def get_logo_url(employer):
    site_url = search_athletics_domain(
        employer
    )

    if not site_url:
        print(
            "No official athletics site found for {}".format(
                employer
            )
        )
        return ""

    logo_url = find_logo_on_athletics_site(
        site_url
    )

    if not logo_url:
        print(
            "No logo found on athletics site for {}".format(
                employer
            )
        )

    return logo_url

# Retrieve the RSS feed.
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
