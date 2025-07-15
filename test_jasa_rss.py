#!/usr/bin/env python3
"""
Test script to specifically test JASA RSS feed access
"""

from app.scrapers import JASAScraper

def test_jasa_rss():
    print("Testing JASA RSS Feed Access...")
    print("=" * 50)
    
    scraper = JASAScraper()
    
    # Test RSS feed access directly
    print("\nTesting RSS feeds...")
    papers = scraper.try_rss_feed()
    
    if papers:
        print(f"✓ SUCCESS: Found {len(papers)} papers via RSS")
        print("\nSample papers:")
        for i, paper in enumerate(papers[:3], 1):
            print(f"{i}. {paper['title']}")
            print(f"   URL: {paper.get('url', 'N/A')}")
            print(f"   Source: {paper.get('source', 'N/A')}")
            print()
    else:
        print("✗ FAILED: No papers found via RSS")
    
    # Test full scraper method
    print("\nTesting full scraper method...")
    all_papers = scraper.scrape_papers()
    
    if all_papers:
        print(f"✓ SUCCESS: Full scraper found {len(all_papers)} papers")
        print("\nFirst few papers:")
        for i, paper in enumerate(all_papers[:5], 1):
            print(f"{i}. {paper['title']}")
            print(f"   Source: {paper.get('source', 'Direct scraping')}")
            print()
    else:
        print("✗ FAILED: Full scraper found no papers")
    
    print("=" * 50)
    return all_papers

if __name__ == "__main__":
    papers = test_jasa_rss()
    if papers:
        print(f"FINAL RESULT: {len(papers)} papers available for JASA")
    else:
        print("FINAL RESULT: JASA access is blocked - need alternative methods")