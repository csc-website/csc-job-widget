import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from html import unescape

FEED_URL = "https://careercenter.collegesportscommunicators.com/jobs?display=rss"
DOMAIN_CACHE_FILE = "logo_domains.json"
MAX_JOBS = 10

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0 Safari/537.36"
)

def clean_text(text):
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())

def fetch(url, timeout=20):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    response = urllib.request.urlopen(request, timeout=timeout)
    data = response.read()
    response.close()
    return data

def load_domain_cache():
    try:
        with open(DOMAIN_CACHE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}

def save_domain_cache(cache):
    with open(DOMAIN_CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache, file, indent=2, ensure_ascii=False, sort_keys=True)

def domain_from_url(url):
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""

def search_athletics_site(employer):
    query = urllib.parse.quote_plus(
        '"' + employer + '" official athletics'
    )

    search_url = (
        "https://html.duckduckgo.com/html/?q="
        + query
    )

    try:
        html = fetch(search_url).decode(
            "utf-8",
            errors="replace"
        )
    except Exception as error:
        print(
            "Athletics search failed for {}: {}".format(
                employer,
                error
            )
        )
        return ""

    # DuckDuckGo HTML results use result__a links. Some results are
    # redirect URLs containing uddg=; unwrap those when necessary.
    links = re.findall(
        r'<a[^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )

    ignored = {
        "duckduckgo.com",
        "google.com",
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "youtube.com",
        "twitter.com",
        "x.com",
        "wikipedia.org",
        "espn.com",
        "ncaa.com",
        "cbssports.com",
        "yahoo.com",
        "usatoday.com",
        "news.google.com",
    }

    candidates = []

    for link in links:
        link = unescape(link)

        parsed = urllib.parse.urlparse(link)

        if "uddg" in urllib.parse.parse_qs(parsed.query):
            link = urllib.parse.parse_qs(parsed.query)["uddg"][0]

        domain = domain_from_url(link)

        if not domain:
            continue

        if domain in ignored:
            continue

        if any(domain.endswith("." + item) for item in ignored):
            continue

        score = 0
        lower = link.lower()

        if "athletic" in lower:
            score += 10

        if "sports" in lower:
            score += 8

        if "official" in lower:
            score += 2

        # Prefer .edu when the athletics site is hosted directly there.
        if domain.endswith(".edu"):
            score += 3

        candidates.append(
            (score, domain)
        )

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    seen = set()

    for score, domain in candidates:

        if domain in seen:
            continue

        seen.add(domain)

        site_url = "https://" + domain + "/"

        try:
            site_html = fetch(site_url).decode(
                "utf-8",
                errors="replace"
            )
        except Exception:
            continue

        lower_html = site_html.lower()

        athletics_terms = [
            "athletics",
            "sports",
            "roster",
            "schedule",
            "scoreboard",
            "ncaa",
            "tickets",
        ]

        matches = sum(
            1
            for term in athletics_terms
            if term in lower_html
        )

        if matches >= 1 or score >= 8:
            print(
                "Athletics site for {}: {}".format(
                    employer,
                    site_url
                )
            )
            return site_url

    return ""

def find_logo(site_url):
    try:
        html = fetch(site_url).decode(
            "utf-8",
            errors="replace"
        )
    except Exception as error:
        print(
            "Could not read athletics site {}: {}".format(
                site_url,
                error
            )
        )
        return ""

    # Prefer actual logo image assets.
    patterns = [
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*(?:class|id|alt)=["\'][^"\']*logo[^"\']*["\']',
        r'<img[^>]+(?:class|id|alt)=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
        r'<img[^>]+src=["\']([^"\']*logo[^"\']*)["\'][^>]*>',
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            html,
            re.IGNORECASE
        )
        if match:
            logo = urllib.parse.urljoin(
                site_url,
                unescape(match.group(1).strip())
            )
            if logo.startswith("http"):
                return logo

    # Open Graph image is a useful fallback and is usually a high-quality
    # athletics brand image.
    meta_patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    ]

    for pattern in meta_patterns:
        match = re.search(
            pattern,
            html,
            re.IGNORECASE
        )
        if match:
            image = urllib.parse.urljoin(
                site_url,
                unescape(match.group(1).strip())
            )
            if image.startswith("http"):
                return image

    return ""

def get_logo(employer, domain_cache):
    site_url = domain_cache.get(employer, "")

    if not site_url:
        site_url = search_athletics_site(employer)

        if site_url:
            domain_cache[employer] = site_url
            save_domain_cache(domain_cache)

    if not site_url:
        print(
            "No athletics site found for {}".format(
                employer
            )
        )
        return ""

    logo = find_logo(site_url)

    if logo:
        print(
            "Logo for {}: {}".format(
                employer,
                logo
            )
        )
    else:
        print(
            "No logo found on athletics site for {}".format(
                employer
            )
        )

    return logo

# Load the RSS feed.
feed = fetch(FEED_URL, timeout=30)
root = ET.fromstring(feed)

domain_cache = load_domain_cache()
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

    logo_url = get_logo(
        employer,
        domain_cache
    )

    jobs.append(
        {
            "title": title,
            "employer": employer,
            "link": link,
            "company_logo_url": logo_url
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
