#!/usr/bin/env python3
"""
Test script to verify the AOS scraper is working correctly
"""

from app.scrapers import AOSScraper

def test_aos_scraper():
    print("Testing AOS Scraper...")
    scraper = AOSScraper()
    papers = scraper.scrape_papers()
    
    print(f"Found {len(papers)} papers")
    print("\nPapers (ordered from latest to oldest):")
    print("=" * 80)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors']) if paper['authors'] else 'No authors found'}")
        print(f"   URL: {paper['url']}")
        print(f"   Journal: {paper['journal']}")
    
    # Check if the latest paper is "Solving the Poisson Equation Using Coupled Markov Chains"
    if papers and "Solving the Poisson Equation Using Coupled Markov Chains" in papers[0]['title']:
        print("\n✅ SUCCESS: Latest paper correctly identified!")
    else:
        print("\n❌ WARNING: Latest paper may not be correctly identified")
        if papers:
            print(f"   Found as latest: {papers[0]['title']}")

if __name__ == "__main__":
    test_aos_scraper()