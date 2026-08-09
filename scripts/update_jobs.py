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

def find_logo(site_url, employer):
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

    # Words that identify the employer's athletics identity. These are
    # derived from the employer name plus common athletics naming patterns.
    employer_words = set(
        re.findall(
            r"[a-z0-9]+",
            employer.lower()
        )
    )

    stop_words = {
        "university",
        "college",
        "athletics",
        "athletic",
        "state",
        "of",
        "the",
        "and",
        "at",
        "campus",
    }

    identity_words = {
        word
        for word in employer_words
        if word not in stop_words and len(word) >= 3
    }

    # Mascot / identity terms commonly present in official athletics
    # branding. These supplement, rather than replace, employer matching.
    mascot_terms = {
        "bulldog", "bulldogs",
        "sooner", "sooners",
        "ute", "utes",
        "flame", "flames",
        "seahawk", "seahawks",
        "shockers",
        "royal", "royals",
        "wildcat", "wildcats",
        "nittany", "lion", "lions",
        "wildcat", "wildcats",
    }

    def is_bad_image(url):
        lower = url.lower()

        bad_terms = [
            "sponsor",
            "smiths",
            "banner",
            "hero",
            "homepage",
            "visit",
            "photo",
            "news",
            "story",
            "article",
            "background",
            "advert",
            "ad-",
            "ncaalogo",
            "ncaa-logo",
        ]

        return any(
            term in lower
            for term in bad_terms
        )

    def text_tokens(value):
        return set(
            re.findall(
                r"[a-z0-9]+",
                value.lower()
            )
        )

    def identity_score(url, context):
        lower = (
            url.lower()
            + " "
            + context.lower()
        )

        tokens = text_tokens(lower)
        score = 0

        # Employer-name matches are strong evidence.
        for word in identity_words:
            if word in tokens:
                score += 15

        # Mascot/brand matches are useful when the employer name itself
        # does not appear in the image filename or alt text.
        for word in mascot_terms:
            if word in tokens:
                score += 8

        preferred_terms = [
            "nav_logo",
            "site.png",
            "site.svg",
            "logo.svg",
            "logo.png",
            "logo.webp",
            "wordmark",
            "athletics-logo",
            "team-logo",
            "primary-logo",
        ]

        for term in preferred_terms:
            if term in lower:
                score += 8

        if "logo" in lower:
            score += 5

        if "wordmark" in lower:
            score += 3

        if is_bad_image(url):
            score -= 60

        return score

    candidates = []

    # Inspect actual image tags and evaluate identity, not just filename.
    for tag in re.findall(
        r"<img\b[^>]*>",
        html,
        re.IGNORECASE
    ):

        src_match = re.search(
            r'\bsrc=["\']([^"\']+)["\']',
            tag,
            re.IGNORECASE
        )

        if not src_match:
            continue

        src = unescape(
            src_match.group(1).strip()
        )

        if not src or src.startswith("data:"):
            continue

        alt_match = re.search(
            r'\balt=["\']([^"\']*)["\']',
            tag,
            re.IGNORECASE
        )

        class_match = re.search(
            r'\bclass=["\']([^"\']*)["\']',
            tag,
            re.IGNORECASE
        )

        id_match = re.search(
            r'\bid=["\']([^"\']*)["\']',
            tag,
            re.IGNORECASE
        )

        context = " ".join(
            [
                alt_match.group(1) if alt_match else "",
                class_match.group(1) if class_match else "",
                id_match.group(1) if id_match else "",
                src,
            ]
        )

        logo = urllib.parse.urljoin(
            site_url,
            src
        )

        if not logo.startswith("http"):
            continue

        score = identity_score(
            logo,
            context
        )

        # Require some evidence of actual logo/branding identity.
        if score >= 12:
            candidates.append(
                (score, logo)
            )

    if candidates:
        candidates.sort(
            key=lambda item: item[0],
            reverse=True
        )

        logo = candidates[0][1]

        print(
            "Selected verified athletics logo for {}: {}".format(
                employer,
                logo
            )
        )

        return logo

    # Try structured metadata containing a logo.
    metadata_patterns = [
        r'<meta[^>]+(?:name|property)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\'](?:og:image|twitter:image)["\']',
    ]

    for pattern in metadata_patterns:
        match = re.search(
            pattern,
            html,
            re.IGNORECASE
        )

        if not match:
            continue

        image = urllib.parse.urljoin(
            site_url,
            unescape(match.group(1).strip())
        )

        if not image.startswith("http"):
            continue

        score = identity_score(
            image,
            image
        )

        if score >= 12:
            print(
                "Using verified athletics metadata image for {}: {}".format(
                    employer,
                    image
                )
            )
            return image

    print(
        "No verified employer-specific athletics logo found for {}".format(
            employer
        )
    )

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

    logo = find_logo(site_url, employer)

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
