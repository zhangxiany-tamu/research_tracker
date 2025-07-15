#!/usr/bin/env python3
"""
Test the new JASA direct scraping with author extraction
"""

import sys
sys.path.append('.')

from app.scrapers import JASAScraper

def test_jasa_direct():
    print("Testing JASA Direct Scraping with Authors...")
    print("=" * 60)
    
    scraper = JASAScraper()
    
    # Test direct page scraping
    print("Testing direct page scraping...")
    papers = scraper.scrape_page(0)
    
    if papers:
        print(f"✓ SUCCESS: Found {len(papers)} papers")
        print("\nSample papers with authors:")
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   Authors: {paper.get('authors', 'No authors')}")
            print(f"   URL: {paper.get('url', 'No URL')}")
            print(f"   DOI: {paper.get('doi', 'No DOI')}")
            print(f"   Source: {paper.get('source', 'Unknown')}")
    else:
        print("✗ FAILED: No papers found")
        
    # Force direct scraping mode
    print("\n" + "="*60)
    print("Testing by disabling RSS and forcing direct scraping...")
    
    # Temporarily disable RSS
    original_rss_method = scraper.try_rss_feed
    scraper.try_rss_feed = lambda: []
    
    all_papers = scraper.scrape_papers()
    
    if all_papers:
        print(f"✓ SUCCESS: Found {len(all_papers)} papers via direct scraping")
        print("\nFirst few papers with authors:")
        for i, paper in enumerate(all_papers[:5], 1):
            print(f"\n{i}. {paper['title']}")
            authors = paper.get('authors', [])
            if authors:
                print(f"   Authors: {', '.join(authors)}")
            else:
                print(f"   Authors: No authors found")
            print(f"   Source: {paper.get('source', 'Unknown')}")
    else:
        print("✗ FAILED: Direct scraping found no papers")
    
    # Restore RSS method
    scraper.try_rss_feed = original_rss_method

if __name__ == "__main__":
    test_jasa_direct()