"""
CrossRef API scrapers for journals blocked by Cloudflare.

Uses the free CrossRef API (https://api.crossref.org/) to fetch paper metadata
for JASA, JRSSB, and Biometrika. No authentication required.
"""

import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class CrossRefScraper:
    """Base class for CrossRef API-based journal scrapers."""

    API_BASE = "https://api.crossref.org/journals"
    MAILTO = "research-tracker@example.com"

    def __init__(self, issn: str, journal_name: str, rows: int = 50):
        self.issn = issn
        self.journal_name = journal_name
        self.rows = rows
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"ResearchTracker/1.0 (mailto:{self.MAILTO})"
        })

    def scrape_papers(self, from_pub_date: Optional[str] = None) -> List[Dict]:
        """
        Fetch recent papers from CrossRef API.

        Args:
            from_pub_date: Optional date string (YYYY-MM-DD) to only fetch papers
                           published on or after this date.

        Returns:
            List of paper dicts in the same format as existing scrapers.
        """
        url = (
            f"{self.API_BASE}/{self.issn}/works"
            f"?sort=published&order=desc&rows={self.rows}"
            f"&mailto={self.MAILTO}"
        )

        if from_pub_date:
            url += f"&filter=from-pub-date:{from_pub_date}"

        print(f"CrossRef [{self.journal_name}]: Fetching {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"CrossRef [{self.journal_name}]: Request failed: {e}")
            return []
        except ValueError as e:
            print(f"CrossRef [{self.journal_name}]: Invalid JSON response: {e}")
            return []

        items = data.get("message", {}).get("items", [])
        print(f"CrossRef [{self.journal_name}]: Got {len(items)} items from API")

        papers = []
        base_time = datetime.utcnow()

        for i, item in enumerate(items):
            paper = self._parse_item(item, base_time, i)
            if paper:
                papers.append(paper)

        print(f"CrossRef [{self.journal_name}]: Parsed {len(papers)} papers")
        return papers

    def _parse_item(self, item: dict, base_time: datetime, index: int) -> Optional[Dict]:
        """Parse a single CrossRef work item into a paper dict."""
        title_list = item.get("title", [])
        if not title_list:
            return None

        title = title_list[0].strip()
        if not title:
            return None

        # Authors
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)

        # DOI and URL
        doi = item.get("DOI")
        paper_url = f"https://doi.org/{doi}" if doi else None

        # Abstract (may contain JATS XML tags)
        abstract = item.get("abstract")
        if abstract:
            abstract = self._strip_jats_tags(abstract)

        # Publication date
        publication_date = self._parse_date(item)

        # PDF URL from links
        pdf_url = None
        for link in item.get("link", []):
            content_type = link.get("content-type", "")
            if "pdf" in content_type:
                pdf_url = link.get("URL")
                break

        # Section / subject area
        subject = item.get("subject", [])
        section = subject[0] if subject else None

        return {
            "title": title,
            "authors": authors,
            "journal": self.journal_name,
            "url": paper_url,
            "doi": doi,
            "abstract": abstract,
            "publication_date": publication_date,
            "scraped_date": base_time - timedelta(seconds=index),
            "section": section,
            "pdf_url": pdf_url,
            "source": "crossref",
        }

    @staticmethod
    def _strip_jats_tags(text: str) -> str:
        """Remove JATS XML tags from abstract text."""
        cleaned = re.sub(r"<[^>]+>", "", text)
        cleaned = cleaned.strip()
        return cleaned

    @staticmethod
    def _parse_date(item: dict) -> Optional[datetime]:
        """Extract the best available publication date from a CrossRef item."""
        # Prefer published-print, then published-online, then published
        for key in ("published-print", "published-online", "published"):
            date_obj = item.get(key)
            if date_obj:
                parts = date_obj.get("date-parts", [[]])[0]
                if parts:
                    year = parts[0]
                    month = parts[1] if len(parts) > 1 else 1
                    day = parts[2] if len(parts) > 2 else 1
                    try:
                        return datetime(year, month, day)
                    except (ValueError, TypeError):
                        continue
        return None


class CrossRefJASAScraper(CrossRefScraper):
    def __init__(self):
        super().__init__(
            issn="1537-274X",
            journal_name="Journal of the American Statistical Association",
            rows=100,
        )


class CrossRefJRSSBScraper(CrossRefScraper):
    def __init__(self):
        super().__init__(
            issn="1467-9868",
            journal_name="Journal of the Royal Statistical Society Series B",
            rows=50,
        )


class CrossRefBiometrikaScraper(CrossRefScraper):
    def __init__(self):
        super().__init__(
            issn="1464-3510",
            journal_name="Biometrika",
            rows=50,
        )
