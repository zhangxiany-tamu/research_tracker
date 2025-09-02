"""
Playwright-based scrapers for journals that block traditional scraping
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin


class PlaywrightJASAScraper:
    """Playwright-based scraper for JASA"""
    
    def __init__(self):
        self.journal_name = "Journal of the American Statistical Association"
        self.base_url = "https://www.tandfonline.com/action/showAxaArticles?journalCode=uasa20"
    
    async def scrape_papers(self) -> List[Dict]:
        """Scrape JASA papers using Playwright"""
        papers = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                # Scrape first 3 pages (most recent papers)
                for page_num in range(3):
                    url = f"{self.base_url}&startPage={page_num}"
                    print(f"JASA Playwright: Fetching page {page_num}...")
                    
                    await page.goto(url, wait_until='domcontentloaded')
                    await asyncio.sleep(3)  # Wait for dynamic content
                    
                    # Check if articles loaded
                    try:
                        await page.wait_for_selector('.tocArticleEntry', timeout=5000)
                    except:
                        print(f"JASA Playwright: No articles found on page {page_num}")
                        break
                    
                    # Get page content
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract articles
                    article_containers = soup.select('.tocArticleEntry')
                    print(f"JASA Playwright: Found {len(article_containers)} articles on page {page_num}")
                    
                    for i, container in enumerate(article_containers):
                        paper_data = self._extract_paper_from_container(container, page_num, i)
                        if paper_data:
                            papers.append(paper_data)
                    
                    # Brief delay between pages
                    if page_num < 2:
                        await asyncio.sleep(2)
                
                await browser.close()
                
        except Exception as e:
            print(f"Error in JASA Playwright scraper: {e}")
        
        print(f"JASA Playwright: Successfully scraped {len(papers)} papers")
        return papers
    
    def _extract_paper_from_container(self, container, page_num: int, index: int) -> Optional[Dict]:
        """Extract paper data from a tocArticleEntry container"""
        try:
            # Extract title
            title_elem = container.select_one('.hlFld-Title')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Extract URL
            title_link = title_elem.find_parent('a')
            url = None
            if title_link:
                href = title_link.get('href')
                if href:
                    url = urljoin(self.base_url, href)
            
            # Extract authors
            authors = []
            author_elements = container.select('.hlFld-ContribAuthor')
            if not author_elements:
                author_elements = container.select('.entryAuthor')
            
            for author_elem in author_elements:
                author_name = author_elem.get_text(strip=True)
                if author_name and author_name not in authors:
                    authors.append(author_name)
            
            # Extract publication date
            publication_date = None
            date_elem = container.select_one('.date')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                if 'Published online:' in date_text:
                    date_part = date_text.replace('Published online:', '').strip()
                    try:
                        publication_date = datetime.strptime(date_part, '%d %b %Y')
                    except ValueError:
                        pass
            
            # Extract DOI
            doi = None
            if url and 'doi' in url:
                doi_match = re.search(r'10\.\d+/[^\s&?]+', url)
                if doi_match:
                    doi = doi_match.group(0)
            
            # Calculate scraped_date for ordering
            order_offset = page_num * 1000 + index
            scraped_date = datetime.utcnow() - timedelta(seconds=order_offset)
            
            return {
                'title': title,
                'url': url,
                'authors': authors,
                'doi': doi,
                'publication_date': publication_date,
                'journal': self.journal_name,
                'scraped_date': scraped_date,
                'order_index': order_offset
            }
            
        except Exception as e:
            print(f"Error extracting JASA paper: {e}")
            return None


class PlaywrightJRSSBScraper:
    """Playwright-based scraper for JRSSB"""
    
    def __init__(self):
        self.journal_name = "Journal of the Royal Statistical Society Series B"
        self.base_url = "https://academic.oup.com/jrsssb/advance-articles"
    
    async def scrape_papers(self) -> List[Dict]:
        """Scrape JRSSB papers using Playwright"""
        papers = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                print(f"JRSSB Playwright: Fetching {self.base_url}...")
                await page.goto(self.base_url, wait_until='domcontentloaded')
                await asyncio.sleep(3)  # Wait for dynamic content
                
                # Wait for articles to load
                try:
                    await page.wait_for_selector('.al-article-item', timeout=5000)
                except:
                    # Try alternative selector
                    try:
                        await page.wait_for_selector('.al-article-box', timeout=5000)
                    except:
                        print("JRSSB Playwright: No articles found")
                        await browser.close()
                        return papers
                
                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find article containers
                article_containers = soup.select('.al-article-item')
                if not article_containers:
                    article_containers = soup.select('.al-article-box')
                
                print(f"JRSSB Playwright: Found {len(article_containers)} articles")
                
                base_time = datetime.utcnow()
                
                for i, container in enumerate(article_containers):
                    paper_data = self._extract_paper_from_container(container, i)
                    if paper_data:
                        # Set scraped_date for ordering
                        paper_data['scraped_date'] = base_time - timedelta(seconds=i)
                        papers.append(paper_data)
                
                await browser.close()
                
        except Exception as e:
            print(f"Error in JRSSB Playwright scraper: {e}")
        
        print(f"JRSSB Playwright: Successfully scraped {len(papers)} papers")
        return papers
    
    def _extract_paper_from_container(self, container, index: int) -> Optional[Dict]:
        """Extract paper data from an article container"""
        try:
            # Extract title and URL
            title_elem = container.select_one('.al-title a')
            if not title_elem:
                # Try alternative selector
                title_elem = container.select_one('.at-articleTitle a')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            href = title_elem.get('href')
            url = f"https://academic.oup.com{href}" if href else None
            
            # Extract authors
            authors = []
            authors_elem = container.select_one('.al-authors-list')
            if authors_elem:
                authors_text = authors_elem.get_text(strip=True)
                # Clean up author names
                authors_text = re.sub(r'\s+and\s+', ', ', authors_text)
                author_parts = authors_text.split(',')
                authors = [name.strip() for name in author_parts if name.strip()]
            
            # Extract publication date
            publication_date = None
            date_elem = container.select_one('.citation-date')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                try:
                    publication_date = datetime.strptime(date_text, '%d %B %Y')
                except ValueError:
                    pass
            
            # Extract DOI
            doi = None
            doi_elem = container.select_one('.al-citation-list')
            if doi_elem:
                doi_text = doi_elem.get_text()
                doi_match = re.search(r'10\.\d+/[^\s]+', doi_text)
                if doi_match:
                    doi = doi_match.group(0)
            
            return {
                'title': title,
                'url': url,
                'authors': authors,
                'doi': doi,
                'publication_date': publication_date,
                'journal': self.journal_name,
                'scraped_date': datetime.utcnow(),
                'order_index': index
            }
            
        except Exception as e:
            print(f"Error extracting JRSSB paper: {e}")
            return None


class PlaywrightBiometrikaScraper:
    """Playwright-based scraper for Biometrika"""
    
    def __init__(self):
        self.journal_name = "Biometrika"
        self.base_url = "https://academic.oup.com/biomet/advance-articles"
    
    async def scrape_papers(self) -> List[Dict]:
        """Scrape Biometrika papers using Playwright"""
        papers = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                print(f"Biometrika Playwright: Fetching {self.base_url}...")
                await page.goto(self.base_url, wait_until='domcontentloaded')
                await asyncio.sleep(3)  # Wait for dynamic content
                
                # Wait for articles to load
                try:
                    await page.wait_for_selector('.al-article-box', timeout=5000)
                except:
                    # Try alternative selector
                    try:
                        await page.wait_for_selector('.al-article-item', timeout=5000)
                    except:
                        print("Biometrika Playwright: No articles found")
                        await browser.close()
                        return papers
                
                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find article containers
                article_containers = soup.select('li.al-article-box')
                if not article_containers:
                    article_containers = soup.select('.al-article-item')
                
                print(f"Biometrika Playwright: Found {len(article_containers)} articles")
                
                base_time = datetime.utcnow()
                
                for i, container in enumerate(article_containers):
                    paper_data = self._extract_paper_from_container(container, i)
                    if paper_data:
                        # Set scraped_date for ordering
                        paper_data['scraped_date'] = base_time - timedelta(seconds=i)
                        papers.append(paper_data)
                
                await browser.close()
                
        except Exception as e:
            print(f"Error in Biometrika Playwright scraper: {e}")
        
        print(f"Biometrika Playwright: Successfully scraped {len(papers)} papers")
        return papers
    
    def _extract_paper_from_container(self, container, index: int) -> Optional[Dict]:
        """Extract paper data from an article container"""
        try:
            # Extract title and URL
            title_elem = container.select_one('.at-articleTitle a')
            if not title_elem:
                # Try alternative selector
                title_elem = container.select_one('.al-title a')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            href = title_elem.get('href')
            url = f"https://academic.oup.com{href}" if href else None
            
            # Extract authors
            authors = []
            authors_elem = container.select_one('.al-authors-list')
            if not authors_elem:
                authors_elem = container.select_one('.at-authors')
            
            if authors_elem:
                authors_text = authors_elem.get_text(strip=True)
                # Clean up author names
                authors_text = re.sub(r'\s+and\s+', ', ', authors_text)
                author_parts = authors_text.split(',')
                authors = [name.strip() for name in author_parts if name.strip()]
            
            # Extract publication date
            publication_date = None
            date_elem = container.select_one('.citation-date')
            if not date_elem:
                date_elem = container.select_one('.at-CitationDate')
            
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                try:
                    publication_date = datetime.strptime(date_text, '%d %B %Y')
                except ValueError:
                    pass
            
            # Extract DOI
            doi = None
            doi_elem = container.select_one('.at-Doi')
            if not doi_elem:
                doi_elem = container.select_one('.al-citation-list')
            
            if doi_elem:
                doi_text = doi_elem.get_text()
                doi_match = re.search(r'10\.\d+/[^\s]+', doi_text)
                if doi_match:
                    doi = doi_match.group(0)
            
            return {
                'title': title,
                'url': url,
                'authors': authors,
                'doi': doi,
                'publication_date': publication_date,
                'journal': self.journal_name,
                'scraped_date': datetime.utcnow(),
                'order_index': index
            }
            
        except Exception as e:
            print(f"Error extracting Biometrika paper: {e}")
            return None


# Wrapper functions to run async scrapers synchronously
def scrape_jasa_with_playwright() -> List[Dict]:
    """Synchronous wrapper for JASA Playwright scraper"""
    scraper = PlaywrightJASAScraper()
    try:
        # Check if we're already in an event loop (FastAPI environment)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new task and run it in the existing loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, scraper.scrape_papers())
                return future.result()
        else:
            return asyncio.run(scraper.scrape_papers())
    except RuntimeError:
        # Fallback to asyncio.run if get_event_loop fails
        return asyncio.run(scraper.scrape_papers())


def scrape_jrssb_with_playwright() -> List[Dict]:
    """Synchronous wrapper for JRSSB Playwright scraper"""
    scraper = PlaywrightJRSSBScraper()
    try:
        # Check if we're already in an event loop (FastAPI environment)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new task and run it in the existing loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, scraper.scrape_papers())
                return future.result()
        else:
            return asyncio.run(scraper.scrape_papers())
    except RuntimeError:
        # Fallback to asyncio.run if get_event_loop fails
        return asyncio.run(scraper.scrape_papers())


def scrape_biometrika_with_playwright() -> List[Dict]:
    """Synchronous wrapper for Biometrika Playwright scraper"""
    scraper = PlaywrightBiometrikaScraper()
    try:
        # Check if we're already in an event loop (FastAPI environment)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new task and run it in the existing loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, scraper.scrape_papers())
                return future.result()
        else:
            return asyncio.run(scraper.scrape_papers())
    except RuntimeError:
        # Fallback to asyncio.run if get_event_loop fails
        return asyncio.run(scraper.scrape_papers())