import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

class BaseScraper:
    def __init__(self, journal_name: str, base_url: str):
        self.journal_name = journal_name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def scrape_papers(self) -> List[Dict]:
        raise NotImplementedError

class AOSScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            "Annals of Statistics",
            "https://imstat.org/journals-and-publications/annals-of-statistics/annals-of-statistics-future-papers/"
        )
    
    def scrape_papers(self) -> List[Dict]:
        papers = []
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links that point to paper PDFs
            paper_links = soup.find_all('a', href=True)
            
            for i, link in enumerate(paper_links):
                href = link.get('href', '')
                if 'e-publications.org' in href and ('confirm' in href or 'confirmation' in href):
                    title = link.get_text(strip=True)
                    
                    # Find authors using the table structure
                    authors = []
                    
                    # The paper is in a table row with 2 cells: title and authors
                    parent_td = link.parent
                    if parent_td and parent_td.name == 'td':
                        table_row = parent_td.find_parent('tr')
                        if table_row:
                            cells = table_row.find_all('td')
                            if len(cells) >= 2:
                                # Authors are in the second cell
                                author_text = cells[1].get_text(strip=True)
                                
                                if author_text:
                                    # Parse the author text
                                    # Split by commas and 'and'
                                    author_parts = re.split(r',|\sand\s', author_text)
                                    authors = [name.strip() for name in author_parts 
                                             if name.strip() and len(name.strip()) > 2]
                    
                    if title:  # Only add if we have a title
                        paper_data = {
                            'title': title,
                            'url': href,
                            'authors': authors,
                            'journal': self.journal_name,
                            'scraped_date': datetime.utcnow(),
                            'order_index': i  # To maintain order from the page
                        }
                        papers.append(paper_data)
            
            # Reverse the order so the latest (bottom of page) appears first
            papers.reverse()
                
        except Exception as e:
            print(f"Error scraping AOS: {e}")
            import traceback
            traceback.print_exc()
        
        return papers

class JMLRScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            "Journal of Machine Learning Research",
            "https://www.jmlr.org/"
        )
    
    def scrape_papers(self) -> List[Dict]:
        """Scrape papers from JMLR latest papers section"""
        papers = []
        try:
            print(f"Attempting to scrape {self.journal_name} from {self.base_url}")
            
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            print(f"Successfully accessed {self.journal_name} (Status: {response.status_code})")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the "Latest papers" section
            latest_heading = None
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                if 'latest papers' in heading.get_text().lower():
                    latest_heading = heading
                    break
            
            if not latest_heading:
                print(f"No 'Latest papers' section found for {self.journal_name}")
                return papers
            
            print(f"Found 'Latest papers' section")
            
            # Get all content after the heading until next h2
            current = latest_heading.next_sibling
            paper_order = 0  # Track paper order to preserve website ordering
            
            while current:
                if current.name == 'p':
                    # Look for all dl elements in this p
                    dl_elements = current.find_all('dl')
                    for dl in dl_elements:
                        dt_elements = dl.find_all('dt')
                        dd_elements = dl.find_all('dd')
                        
                        for i in range(len(dt_elements)):
                            if i < len(dd_elements):
                                paper_data = self._parse_jmlr_paper(dt_elements[i], dd_elements[i], paper_order)
                                if paper_data:
                                    papers.append(paper_data)
                                    print(f"Extracted: {paper_data['title'][:50]}...")
                                    paper_order += 1
                
                current = current.next_sibling
                if current and current.name == 'h2':  # Stop at next heading
                    break
            
            print(f"Successfully scraped {len(papers)} papers from {self.journal_name}")
            
        except Exception as e:
            print(f"Error scraping {self.journal_name}: {e}")
        
        return papers
    
    def _parse_jmlr_paper(self, dt_element, dd_element, paper_order=0) -> Optional[Dict]:
        """Extract paper data from dt (title) and dd (authors/links) elements"""
        try:
            # Extract title
            title = dt_element.get_text(strip=True)
            
            # Extract authors and year from dd element
            dd_text = dd_element.get_text(strip=True)
            
            # Extract authors (before year)
            authors = []
            year = None
            
            # Look for year patterns (2025, 2024, etc.)
            # Handle both formats: ", 2025. [" and ", 2025.("
            year_match = re.search(r', (\d{4})\.\s*[\[\(]', dd_text)
            if year_match:
                year = int(year_match.group(1))
                authors_text = dd_text.split(f', {year}.')[0]
                
                # Split authors by comma and clean
                author_parts = [name.strip() for name in authors_text.split(',')]
                authors = [name for name in author_parts if name]
            
            # Extract links
            url = None
            pdf_url = None
            bib_url = None
            
            links = dd_element.find_all('a')
            for link in links:
                href = link.get('href', '')
                link_text = link.get_text(strip=True).lower()
                
                if link_text == 'abs' and not url:
                    url = f"https://www.jmlr.org{href}" if href.startswith('/') else href
                elif link_text == 'pdf' and not pdf_url:
                    pdf_url = f"https://www.jmlr.org{href}" if href.startswith('/') else href
                elif link_text == 'bib' and not bib_url:
                    bib_url = f"https://www.jmlr.org{href}" if href.startswith('/') else href
            
            # Fetch abstract and BibTeX from [abs] and [bib] links
            abstract = None
            bibtex = None
            publication_date = None
            
            # Get abstract from [abs] link
            if url:
                abstract = self._fetch_jmlr_abstract(url)
            
            # Get real BibTeX from [bib] link
            if bib_url:
                bibtex = self._fetch_jmlr_bibtex(bib_url)
            
            # Don't set publication dates - BibTeX doesn't contain real submission/revision/publication dates
            # The real dates are in PDF headers but are complex to extract reliably
            
            # Use paper_order to create a timestamp that preserves website order
            # Papers at the beginning of the list should have later timestamps
            base_time = datetime.utcnow()
            # Subtract seconds based on paper order so earlier papers get later timestamps
            ordered_time = base_time - timedelta(seconds=paper_order)
            
            return {
                'title': title,
                'url': url,
                'pdf_url': pdf_url,
                'authors': authors,
                'abstract': abstract,  # Fetched from [abs] link
                'bibtex': bibtex,  # Fetched from [bib] link
                'doi': None,  # Not available in listing
                'journal': self.journal_name,
                'publication_date': publication_date,  # No fake dates
                'section': None,  # Not available in listing
                'scraped_date': ordered_time  # Use ordered time to preserve website order
            }
            
        except Exception as e:
            print(f"Error parsing JMLR paper: {e}")
            return None
    
    def _fetch_jmlr_abstract(self, abs_url: str) -> Optional[str]:
        """Fetch abstract from JMLR [abs] link"""
        try:
            response = self.session.get(abs_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the abstract section
            abstract_section = soup.find('div', {'id': 'abstract'})
            if abstract_section:
                return abstract_section.get_text(strip=True)
            
            # Alternative: look for h3 "Abstract" followed by paragraph
            abstract_heading = soup.find('h3', string=re.compile(r'Abstract', re.I))
            if abstract_heading:
                next_p = abstract_heading.find_next('p')
                if next_p:
                    return next_p.get_text(strip=True)
            
            return None
            
        except Exception as e:
            print(f"Error fetching abstract from {abs_url}: {e}")
            return None
    
    def _fetch_jmlr_bibtex(self, bib_url: str) -> Optional[str]:
        """Fetch real BibTeX from JMLR [bib] link"""
        try:
            response = self.session.get(bib_url, timeout=10)
            response.raise_for_status()
            
            # The BibTeX file contains the raw BibTeX content
            bibtex_content = response.text.strip()
            
            # Basic validation that this looks like BibTeX
            if bibtex_content.startswith('@') and '{' in bibtex_content:
                return bibtex_content
            else:
                print(f"Invalid BibTeX format from {bib_url}")
                return None
                
        except Exception as e:
            print(f"Error fetching BibTeX from {bib_url}: {e}")
            return None
    

# Placeholder scrapers for journals that require alternative access methods
class JASAScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            "Journal of the American Statistical Association",
            "https://www.tandfonline.com/action/showAxaArticles?journalCode=uasa20"
        )
        # Enhanced headers (same approach as JRSSB/Biometrika breakthrough)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.tandfonline.com/'
        })
    
    def get_total_pages(self) -> int:
        """Determine the total number of pages available by checking for content"""
        try:
            max_page = 0
            
            # Check pages sequentially until we find an empty page
            for page in range(10):  # Check up to 10 pages
                test_url = f"{self.base_url}&startPage={page}"
                try:
                    print(f"JASA: Checking page {page} for content...")
                    test_response = self.session.get(test_url, timeout=10)
                    
                    if test_response.status_code == 200:
                        test_soup = BeautifulSoup(test_response.content, 'html.parser')
                        
                        # Look for article containers that indicate content
                        articles = test_soup.select('.tocArticleEntry')
                        
                        if articles and len(articles) > 0:
                            max_page = page
                            print(f"JASA: Found {len(articles)} articles on page {page}")
                        else:
                            print(f"JASA: No articles found on page {page}, stopping")
                            break
                    else:
                        print(f"JASA: Page {page} returned status {test_response.status_code}")
                        break
                        
                except Exception as e:
                    print(f"JASA: Error checking page {page}: {e}")
                    break
                    
            print(f"JASA: Total pages found: {max_page + 1} (0 to {max_page})")
            return max_page
            
        except Exception as e:
            print(f"Error determining total pages for JASA: {e}")
            return 0
    
    def scrape_page(self, page_num: int) -> List[Dict]:
        """Scrape papers from a specific page"""
        papers = []
        try:
            # Use a completely fresh session for each page to avoid session-based blocking
            import requests
            import time
            
            # Add longer delay to avoid rate limiting
            if page_num > 0:
                time.sleep(5)  # Increased delay
            
            fresh_session = requests.Session()
            fresh_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.tandfonline.com/'
            })
            
            url = f"{self.base_url}&startPage={page_num}"
            response = fresh_session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # For the advance articles page, use the article container approach
            article_containers = soup.select('.tocArticleEntry')
            print(f"JASA: Found {len(article_containers)} article containers")
            
            if article_containers:
                for container in article_containers:
                    paper_data = self._extract_paper_from_container(container, page_num)
                    if paper_data:
                        papers.append(paper_data)
            else:
                # Fallback to title-based approach
                article_selectors = [
                    '.hlFld-Title',  # Primary selector that worked
                    '.art_title',   # Alternative title selector
                ]
                
                articles = []
                for selector in article_selectors:
                    found = soup.select(selector)
                    if found:
                        articles = found
                        break
                
                for article in articles:
                    paper_data = self._extract_paper_data(article, page_num)
                    if paper_data:
                        papers.append(paper_data)
                    
        except Exception as e:
            print(f"Error scraping JASA page {page_num}: {e}")
            
        return papers
    
    def _extract_paper_from_container(self, container, page_num: int) -> Optional[Dict]:
        """Extract paper data from a tocArticleEntry container (for advance articles page)"""
        try:
            # Extract title
            title_elem = container.select_one('.hlFld-Title')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Extract URL from title link
            title_link = title_elem.find_parent('a')
            url = None
            if title_link:
                href = title_link.get('href')
                if href:
                    url = urljoin(self.base_url, href)
            
            # Extract authors using the selectors we found
            authors = []
            author_selectors = ['.hlFld-ContribAuthor', '.entryAuthor']
            
            for selector in author_selectors:
                author_elements = container.select(selector)
                if author_elements:
                    for author_elem in author_elements:
                        author_name = author_elem.get_text(strip=True)
                        if author_name and author_name not in authors:
                            authors.append(author_name)
                    break  # Use first selector that works
            
            # Extract DOI if available
            doi = None
            if url and 'doi' in url:
                doi_match = re.search(r'10\.[0-9]{4}\/[^\s]+', url)
                if doi_match:
                    doi = doi_match.group(0)
            
            return {
                'title': title,
                'url': url,
                'authors': authors,
                'doi': doi,
                'journal': self.journal_name,
                'scraped_date': datetime.utcnow(),
                'page_number': page_num,
                'source': 'direct_scraping'
            }
            
        except Exception as e:
            print(f"Error extracting paper from container: {e}")
            return None
    
    def _extract_paper_data(self, article_element, page_num: int) -> Optional[Dict]:
        """Extract paper data from an article element"""
        try:
            # For JASA, try specific selectors first, then general ones
            title = None
            
            # If this is a .hlFld-Title element, get the text directly
            if 'hlFld-Title' in str(article_element.get('class', [])):
                title_link = article_element.find('a')
                if title_link:
                    title = title_link.get_text(strip=True)
            
            # If not found, try other selectors
            if not title:
                title_selectors = [
                    'a',  # Direct link
                    'h2 a', 'h3 a', 'h4 a',
                    'a.title', 'a.articleTitle',
                    '.title a', '.articleTitle a',
                    'a[href*="doi"]', 'a[href*="abs"]',
                    'h2', 'h3', 'h4',
                    '.title', '.articleTitle'
                ]
                
                for selector in title_selectors:
                    title_elem = article_element.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title and len(title) > 10:  # Reasonable title length
                            break
            
            if not title:
                return None
            
            # Try to find URL
            url = None
            url_selectors = [
                'a[href*="doi"]', 'a[href*="abs"]', 'a[href*="full"]',
                'h2 a', 'h3 a', '.title a'
            ]
            
            for selector in url_selectors:
                url_elem = article_element.select_one(selector)
                if url_elem:
                    href = url_elem.get('href')
                    if href:
                        url = urljoin(self.base_url, href)
                        break
            
            # Try to find authors
            authors = []
            author_selectors = [
                '.author', '.authors', '.authorName',
                '.author-name', '.citation-author',
                '[class*="author"]', '[class*="Author"]'
            ]
            
            for selector in author_selectors:
                author_elements = article_element.select(selector)
                if author_elements:
                    for elem in author_elements:
                        author_text = elem.get_text(strip=True)
                        if author_text:
                            # Split by common separators
                            author_parts = re.split(r',|\sand\s|\&', author_text)
                            authors.extend([name.strip() for name in author_parts if name.strip()])
                    break
            
            # Try to find abstract
            abstract = None
            abstract_selectors = [
                '.abstract', '.summary', '.description',
                '[class*="abstract"]', '[class*="summary"]'
            ]
            
            for selector in abstract_selectors:
                abstract_elem = article_element.select_one(selector)
                if abstract_elem:
                    abstract = abstract_elem.get_text(strip=True)
                    if abstract and len(abstract) > 50:  # Reasonable abstract length
                        break
            
            # Try to find DOI
            doi = None
            doi_patterns = [
                r'doi[:\s]*([0-9]{2}\.[0-9]{4}\/[^\s]+)',
                r'10\.[0-9]{4}\/[^\s]+',
            ]
            
            article_text = article_element.get_text()
            for pattern in doi_patterns:
                match = re.search(pattern, article_text, re.I)
                if match:
                    doi = match.group(1) if match.groups() else match.group(0)
                    break
            
            return {
                'title': title,
                'url': url,
                'authors': authors,
                'abstract': abstract,
                'doi': doi,
                'journal': self.journal_name,
                'scraped_date': datetime.utcnow(),
                'page_number': page_num
            }
            
        except Exception as e:
            print(f"Error extracting paper data: {e}")
            return None
    
    def try_rss_feed(self) -> List[Dict]:
        """Try to access JASA via RSS feed"""
        papers = []
        
        # Common RSS feed URLs for Taylor & Francis journals
        rss_urls = [
            f"https://www.tandfonline.com/feed/rss/uasa20",
            f"https://www.tandfonline.com/action/showFeed?type=etoc&feed=rss&jc=uasa20",
            f"https://www.tandfonline.com/toc/uasa20/current",
            f"https://www.tandfonline.com/loi/uasa20/rss"
        ]
        
        for rss_url in rss_urls:
            try:
                print(f"JASA: Trying RSS feed: {rss_url}")
                response = self.session.get(rss_url, timeout=10)
                
                if response.status_code == 200:
                    # Try to parse as XML/RSS
                    try:
                        from xml.etree import ElementTree as ET
                        root = ET.fromstring(response.content)
                        
                        # Look for RSS items
                        for item in root.findall('.//item'):
                            title_elem = item.find('title')
                            link_elem = item.find('link')
                            description_elem = item.find('description')
                            pubDate_elem = item.find('pubDate')
                            
                            if title_elem is not None and title_elem.text:
                                paper_data = {
                                    'title': title_elem.text.strip(),
                                    'url': link_elem.text.strip() if link_elem is not None else None,
                                    'abstract': description_elem.text.strip() if description_elem is not None else None,
                                    'authors': [],  # RSS usually doesn't include detailed author info
                                    'journal': self.journal_name,
                                    'scraped_date': datetime.utcnow(),
                                    'source': 'RSS'
                                }
                                papers.append(paper_data)
                        
                        if papers:
                            print(f"JASA: Successfully found {len(papers)} papers via RSS")
                            return papers
                            
                    except ET.ParseError:
                        # Not valid XML, try HTML parsing
                        soup = BeautifulSoup(response.content, 'html.parser')
                        # Look for article links or content
                        articles = soup.find_all('a', href=True)
                        for article in articles:
                            href = article.get('href')
                            title = article.get_text(strip=True)
                            
                            # Filter for actual papers (not PDF links, abstracts, etc.)
                            if (href and 'doi' in href and 'full' in href and 
                                title and len(title) > 20 and 
                                not any(skip in title.lower() for skip in ['pdf', 'abstract', 'supplemental', 'doi:', 'mb)'])):
                                
                                paper_data = {
                                    'title': title,
                                    'url': urljoin(self.base_url, href),
                                    'authors': [],
                                    'journal': self.journal_name,
                                    'scraped_date': datetime.utcnow(),
                                    'source': 'RSS_HTML'
                                }
                                papers.append(paper_data)
                        
                        if papers:
                            print(f"JASA: Successfully found {len(papers)} papers via RSS HTML")
                            return papers
                        
            except Exception as e:
                print(f"JASA: RSS feed {rss_url} failed: {e}")
                continue
        
        return papers
    
    def scrape_papers(self) -> List[Dict]:
        """Scrape all papers from all available pages"""
        papers = []
        
        # Try direct scraping first (better author extraction)
        print("JASA: Attempting direct scraping...")
        
        try:
            # Get base timestamp for ordering
            base_time = datetime.utcnow()
            
            # Try scraping pages until we get an empty page or error
            for page_num in range(15):  # Try up to 15 pages
                try:
                    print(f"JASA: Scraping page {page_num}...")
                    page_papers = self.scrape_page(page_num)
                    
                    if not page_papers:
                        print(f"JASA: Page {page_num} empty, stopping")
                        break
                    
                    # Add page-specific ordering to maintain proper sequence
                    for i, paper in enumerate(page_papers):
                        # Papers at top of page are newer, so lower index = newer
                        # Page 0 is newest, so we want page 0 papers first
                        paper['page_order'] = page_num * 1000 + i
                        
                        # Set scraped_date to preserve ordering: newer papers get later timestamps
                        # Subtract seconds to make page 0 papers have the highest timestamps
                        order_offset = paper['page_order']
                        paper['scraped_date'] = base_time - timedelta(seconds=order_offset)
                    
                    papers.extend(page_papers)
                    print(f"JASA: Page {page_num} yielded {len(page_papers)} papers")
                    
                    # Be respectful - add delay between requests  
                    import time
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"JASA: Error on page {page_num}: {e}")
                    break
                
            # Sort by page_order to ensure newest papers (page 0, top of page) come first
            papers.sort(key=lambda p: p.get('page_order', 999999))
            
            print(f"JASA: Successfully scraped {len(papers)} papers via direct scraping")
            
            if papers:
                return papers
                    
        except Exception as e:
            print(f"JASA direct scraping error: {e}")
        
        # If direct scraping fails, try RSS feeds as backup
        print("JASA: Direct scraping failed, attempting RSS feed access...")
        papers = self.try_rss_feed()
        
        if papers:
            return papers
        
        # Final fallback
        print("JASA: All methods failed")
        return papers

class JRSSBScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            "Journal of the Royal Statistical Society Series B",
            "https://academic.oup.com/jrsssb/advance-articles"
        )
        # Enhanced session with working headers (same approach as JASA breakthrough)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://academic.oup.com/'
        })
    
    def scrape_papers(self) -> List[Dict]:
        """Scrape papers from JRSSB advance articles page"""
        papers = []
        
        try:
            print("JRSSB: Attempting direct scraping...")
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article containers
            article_containers = soup.select('.al-article-items')
            print(f"JRSSB: Found {len(article_containers)} article containers")
            
            base_time = datetime.utcnow()
            
            for i, container in enumerate(article_containers):
                paper_data = self._extract_paper_from_container(container, i)
                if paper_data:
                    # Set scraped_date to preserve ordering (first article = newest)
                    paper_data['scraped_date'] = base_time - timedelta(seconds=i)
                    papers.append(paper_data)
            
            print(f"JRSSB: Successfully scraped {len(papers)} papers")
            return papers
            
        except Exception as e:
            print(f"Error scraping JRSSB: {e}")
            return []
    
    def _extract_paper_from_container(self, container, index: int) -> Optional[Dict]:
        """Extract paper data from an al-article-items container"""
        try:
            # Extract title and URL
            title_elem = container.select_one('.al-title a')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            href = title_elem.get('href')
            url = f"https://academic.oup.com{href}" if href else None
            
            # Extract authors from .al-authors-list
            authors = []
            authors_elem = container.select_one('.al-authors-list')
            if authors_elem:
                # Replace delimiter spans with spaced text before parsing
                authors_html = str(authors_elem)
                authors_html = authors_html.replace('<span class="al-author-delim">and</span>', ' and ')
                authors_html = authors_html.replace('<span class="al-author-delim">and others</span>', ' and others')
                
                temp_soup = BeautifulSoup(authors_html, 'html.parser')
                authors_text = temp_soup.get_text(strip=True)
                
                # Split by "and" with proper spacing
                author_parts = re.split(r'\s+and\s+', authors_text)
                authors = [name.strip() for name in author_parts if name.strip()]
                
                # Ensure consistent ordering: move "others" to the end
                if 'others' in authors:
                    authors = [name for name in authors if name != 'others'] + ['others']
            
            # Extract publication date (from Published: field, not al-pub-date)
            publication_date = None
            published_date_elem = container.select_one('.ww-citation-date-wrap .citation-date')
            if published_date_elem:
                date_text = published_date_elem.get_text(strip=True)
                try:
                    # Parse date like "4 July 2025"
                    publication_date = datetime.strptime(date_text, '%d %B %Y')
                except ValueError:
                    # If parsing fails, just store as text
                    pass
            
            # Extract article type
            article_type = None
            type_elem = container.select_one('.sri-type')
            if type_elem:
                article_type = type_elem.get_text(strip=True)
            
            # Extract section information
            section = None
            section_pubinfo = container.select('.al-article-pubinfo')
            for pubinfo in section_pubinfo:
                if 'Section:' in pubinfo.get_text():
                    section_link = pubinfo.select_one('a')
                    if section_link:
                        section = section_link.get_text(strip=True)
                    break
            
            # Extract DOI from citation
            doi = None
            citation_elem = container.select_one('.al-citation-list')
            if citation_elem:
                citation_text = citation_elem.get_text()
                doi_match = re.search(r'10\.[0-9]{4}/[^\s]+', citation_text)
                if doi_match:
                    doi = doi_match.group(0)
            
            return {
                'title': title,
                'url': url,
                'authors': authors,
                'doi': doi,
                'publication_date': publication_date,
                'article_type': article_type,
                'section': section,
                'journal': self.journal_name,
                'scraped_date': datetime.utcnow(),
                'order_index': index
            }
            
        except Exception as e:
            print(f"Error extracting JRSSB paper from container: {e}")
            return None

class BiometrikaScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            "Biometrika",
            "https://academic.oup.com/biomet/advance-articles"
        )
        
        # Use enhanced headers (same as JASA/JRSSB breakthrough)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://academic.oup.com/'
        })
    
    def scrape_papers(self) -> List[Dict]:
        """Scrape papers from Biometrika advance articles using JRSSB approach"""
        papers = []
        
        try:
            print(f"Attempting to scrape {self.journal_name} from {self.base_url}")
            
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            print(f"Successfully accessed {self.journal_name} (Status: {response.status_code})")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find paper containers (Biometrika uses li.al-article-box)
            paper_containers = soup.find_all('li', class_='al-article-box')
            
            if not paper_containers:
                print(f"No paper containers found for {self.journal_name}")
                return papers
                
            print(f"Found {len(paper_containers)} paper containers")
            
            for container in paper_containers:
                paper_data = self._extract_paper_data(container)
                if paper_data:
                    papers.append(paper_data)
                    print(f"Extracted: {paper_data['title'][:50]}...")
                    
            print(f"Successfully scraped {len(papers)} papers from {self.journal_name}")
            
        except requests.RequestException as e:
            print(f"Network error accessing {self.journal_name}: {e}")
        except Exception as e:
            print(f"Error scraping {self.journal_name}: {e}")
            
        return papers
    
    def _extract_paper_data(self, container) -> Dict:
        """Extract paper data from a container element (same approach as JRSSB)"""
        try:
            # Extract title (Biometrika structure: h5 inside al-article-items)
            title_elem = container.find('h5') or container.find('h4')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a')
            if not title_link:
                return None
                
            title = title_link.get_text(strip=True)
            relative_url = title_link.get('href')
            
            # Construct full URL
            if relative_url.startswith('/'):
                url = f"https://academic.oup.com{relative_url}"
            else:
                url = relative_url
            
            # Extract authors (same complex HTML structure as JRSSB)
            authors = []
            authors_elem = container.find('div', class_='al-authors-list')
            if authors_elem:
                # Handle complex HTML structure with delimiters
                authors_html = str(authors_elem)
                authors_html = authors_html.replace('<span class="al-author-delim">and</span>', ' and ')
                authors_html = authors_html.replace('<span class="al-author-delim">and others</span>', ' and others')
                
                # Parse the cleaned HTML
                temp_soup = BeautifulSoup(authors_html, 'html.parser')
                authors_text = temp_soup.get_text(strip=True)
                
                # Split by 'and' to get individual authors
                if authors_text:
                    author_parts = re.split(r'\s+and\s+', authors_text)
                    authors = [name.strip() for name in author_parts if name.strip()]
                    
                    # Ensure consistent ordering with "others" at the end
                    if 'others' in authors:
                        authors = [name for name in authors if name != 'others'] + ['others']
            
            # Extract publication date (Biometrika structure: span.al-pub-date)
            publication_date = None
            date_elem = container.find('span', class_='al-pub-date')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                try:
                    publication_date = datetime.strptime(date_text, '%d %B %Y')
                except ValueError:
                    try:
                        publication_date = datetime.strptime(date_text, '%B %d, %Y')
                    except ValueError:
                        print(f"Could not parse date: {date_text}")
            
            # Extract section information (Biometrika structure: span.sri-type)
            section = None
            section_elem = container.find('span', class_='sri-type')
            if section_elem:
                section = section_elem.get_text(strip=True)
            
            # Extract abstract (if available)
            abstract = None
            abstract_elem = container.find('div', class_='al-preview') or container.find('div', class_='abstract')
            if abstract_elem:
                abstract = abstract_elem.get_text(strip=True)
            
            return {
                'title': title,
                'url': url,
                'authors': authors,
                'abstract': abstract,
                'doi': None,  # DOI extraction could be added if needed
                'journal': self.journal_name,
                'publication_date': publication_date,
                'section': section,
                'scraped_date': datetime.utcnow()
            }
            
        except Exception as e:
            print(f"Error extracting Biometrika paper from container: {e}")
            return None

def get_all_scrapers():
    return [
        AOSScraper(),
        JMLRScraper(),
        JASAScraper(),
        JRSSBScraper(),
        BiometrikaScraper()
    ]