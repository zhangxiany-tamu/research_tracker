#!/usr/bin/env python3
"""
Test script to verify the JASA scraper can access the website and extract papers
"""

from app.scrapers import JASAScraper
import time

def test_jasa_scraper():
    print("Testing JASA Scraper...")
    print("=" * 60)
    
    scraper = JASAScraper()
    
    # Test 1: Check if we can access the site
    print("\n1. Testing site access...")
    try:
        total_pages = scraper.get_total_pages()
        print(f"   ✓ Site accessible - Found {total_pages} pages")
    except Exception as e:
        print(f"   ✗ Site access failed: {e}")
        return
    
    if total_pages == 0:
        print("   ✗ No pages found - likely blocked or no articles")
        return
    
    # Test 2: Try to scrape first page
    print("\n2. Testing first page scraping...")
    try:
        page_papers = scraper.scrape_page(0)
        print(f"   ✓ First page scraped - Found {len(page_papers)} papers")
        
        if page_papers:
            print("\n   Sample paper from first page:")
            sample = page_papers[0]
            print(f"   Title: {sample.get('title', 'N/A')}")
            print(f"   Authors: {sample.get('authors', 'N/A')}")
            print(f"   URL: {sample.get('url', 'N/A')}")
            print(f"   DOI: {sample.get('doi', 'N/A')}")
            
    except Exception as e:
        print(f"   ✗ First page scraping failed: {e}")
        return
    
    # Test 3: Try full scraping (with limit for testing)
    print("\n3. Testing full scraping (first 2 pages only)...")
    try:
        # Temporarily limit to first 2 pages for testing
        original_method = scraper.scrape_papers
        
        def limited_scrape():
            papers = []
            max_pages = min(2, total_pages + 1)
            
            for page_num in range(max_pages):
                print(f"   Scraping page {page_num}...")
                page_papers = scraper.scrape_page(page_num)
                papers.extend(page_papers)
                time.sleep(0.5)  # Be respectful
            
            return papers
        
        papers = limited_scrape()
        print(f"   ✓ Limited scraping completed - Found {len(papers)} total papers")
        
        if papers:
            print(f"\n   All papers found:")
            for i, paper in enumerate(papers[:5], 1):  # Show first 5
                print(f"   {i}. {paper.get('title', 'No title')}")
                authors = paper.get('authors', [])
                if authors:
                    print(f"      Authors: {', '.join(authors[:3])}")
                    if len(authors) > 3:
                        print(f"               ... and {len(authors) - 3} more")
                print()
        
    except Exception as e:
        print(f"   ✗ Full scraping failed: {e}")
        return
    
    print("=" * 60)
    print("JASA Scraper Test Complete!")
    
    if papers:
        print("✓ SUCCESS: JASA scraper is working!")
        print(f"  - Found {len(papers)} papers across {min(2, total_pages + 1)} pages")
        print(f"  - Estimated total papers available: {len(papers) * (total_pages + 1) // min(2, total_pages + 1)}")
    else:
        print("✗ FAILED: No papers could be extracted")

if __name__ == "__main__":
    test_jasa_scraper()