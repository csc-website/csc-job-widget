```python
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
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_career_center_logo(html):
    """
    Look specifically for the Career Center's own showLogo.cfm
    employer-logo endpoint.
    """

    patterns = [
        r'https?://[^"\']*showLogo\.cfm[^"\']*',
        r'//[^"\']*showLogo\.cfm[^"\']*',
        r'[^"\']*showLogo\.cfm\?[^"\']*',
    ]

    for pattern in patterns:
        matches = re.findall(
            pattern,
            html,
            re.IGNORECASE,
        )

        if matches:
            logo_url = unescape(matches[0]).strip()

            # Remove any HTML entities or trailing characters
            logo_url = logo_url.replace("&amp;", "&")

            # If the URL is protocol-relative, add https.
            if logo_url.startswith("//"):
                logo_url = "https:" + logo_url

            # If the URL is relative, build the full Career Center URL.
            elif logo_url.startswith("/"):
                logo_url = (
                    "https://careercenter.collegesportscommunicators.com"
                    + logo_url
                )

            # Remove accidental quote/HTML characters.
            logo_url = logo_url.rstrip("'\"<>")

            return logo_url

    return ""


def extract_open_graph_logo(html):
    """
    Fallback: look for the normal Open Graph image.
    """

    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            html,
            re.IGNORECASE,
        )

        if match:
            logo_url = unescape(match.group(1).strip())

            if logo_url.startswith("//"):
                logo_url = "https:" + logo_url

            return logo_url

    return ""


# ------------------------------------------------------------
# Download the Career Center RSS feed
# ------------------------------------------------------------

request = urllib.request.Request(
    FEED_URL,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    },
)

with urllib.request.urlopen(request, timeout=30) as response:
    xml = response.read()


root = ET.fromstring(xml)

jobs = []


# ------------------------------------------------------------
# Process jobs
# ------------------------------------------------------------

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

    # CSC places the employer after a | character.
    if "|" in title:

        title, employer = title.split("|", 1)

        title = title.strip()
        employer = employer.strip()

    else:

        employer = ""

    logo_url = ""

    # --------------------------------------------------------
    # Try to retrieve the individual Career Center job page
    # --------------------------------------------------------

    try:

        print("")
        print("Checking Career Center page for {}:".format(employer))
        print(link)

        page_html = fetch_url(link)

        # ----------------------------------------------------
        # First choice:
        # Career Center's own showLogo.cfm endpoint
        # ----------------------------------------------------

        if "showLogo.cfm" in page_html:

            logo_url = extract_career_center_logo(page_html)

            if logo_url:

                print(
                    "Career Center logo found for {}: {}".format(
                        employer,
                        logo_url,
                    )
                )

            else:

                print(
                    "showLogo.cfm was found, but the logo URL "
                    "could not be extracted for {}".format(
                        employer,
                    )
                )

        # ----------------------------------------------------
        # If no showLogo.cfm was found, check for a challenge
        # ----------------------------------------------------

        elif (
            "captcha" in page_html.lower()
            or "bot check" in page_html.lower()
            or "checking your browser" in page_html.lower()
            or "javascript required" in page_html.lower()
        ):

            print(
                "Career Center returned a bot/challenge page "
                "for {}".format(
                    employer,
                )
            )

        # ----------------------------------------------------
        # Last fallback:
        # normal Open Graph image
        # ----------------------------------------------------

        else:

            logo_url = extract_open_graph_logo(page_html)

            if logo_url:

                print(
                    "Open Graph logo found for {}: {}".format(
                        employer,
                        logo_url,
                    )
                )

            else:

                print(
                    "No Career Center logo found for {}".format(
                        employer,
                    )
                )

    except Exception as error:

        print(
            "Could not retrieve Career Center page for {}: {}".format(
                employer,
                error,
            )
        )

    # --------------------------------------------------------
    # Create job record
    # --------------------------------------------------------

    job = {
        "title": title,
        "employer": employer,
        "link": link,
        "company_logo_url": logo_url,
    }

    jobs.append(job)

    # Keep the existing 10-job limit.
    if len(jobs) == 10:
        break


# ------------------------------------------------------------
# Write jobs.json
# ------------------------------------------------------------

with open(
    "jobs.json",
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        jobs,
        file,
        indent=2,
        ensure_ascii=False,
    )


print("")
print("Updated {} jobs.".format(len(jobs)))
```
