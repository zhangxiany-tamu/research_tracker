#!/usr/bin/env python3
"""
Debug script to understand the HTML structure of the AOS page
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_aos_structure():
    url = "https://imstat.org/journals-and-publications/annals-of-statistics/annals-of-statistics-future-papers/"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all links that point to paper PDFs
    paper_links = soup.find_all('a', href=True)
    
    found_papers = 0
    
    for i, link in enumerate(paper_links):
        href = link.get('href', '')
        if 'e-publications.org' in href and ('confirm' in href or 'confirmation' in href):
            found_papers += 1
            if found_papers <= 3:  # Only show first 3 for debugging
                title = link.get_text(strip=True)
                print(f"\n=== Paper {found_papers}: {title} ===")
                print(f"URL: {href}")
                
                # Show the parent element's HTML structure
                parent = link.parent
                if parent:
                    print(f"Parent tag: {parent.name}")
                    print(f"Parent text:\n{parent.get_text()}")
                    print(f"Parent HTML:\n{parent}")
                    
                    # Look for next siblings
                    print(f"\nNext siblings:")
                    for j, sibling in enumerate(parent.next_siblings):
                        if j < 3:  # Only show first 3 siblings
                            try:
                                if sibling and isinstance(sibling, str):
                                    if sibling.strip():
                                        print(f"  Sibling {j} (text): '{sibling.strip()}'")
                                elif sibling and hasattr(sibling, 'name'):
                                    text = sibling.get_text(strip=True) if hasattr(sibling, 'get_text') else str(sibling)
                                    print(f"  Sibling {j} (element): {sibling.name} - {text[:100]}")
                                else:
                                    print(f"  Sibling {j}: {type(sibling)} - {str(sibling)[:50]}")
                            except Exception as e:
                                print(f"  Sibling {j}: Error - {e}")
                            
                    # Also check the table row structure
                    table_row = parent.find_parent('tr')
                    if table_row:
                        print(f"\nTable row content:")
                        cells = table_row.find_all('td')
                        for k, cell in enumerate(cells):
                            print(f"  Cell {k}: {cell.get_text(strip=True)[:200]}")
                
                print("-" * 50)
    
    print(f"\nTotal papers found: {found_papers}")

if __name__ == "__main__":
    debug_aos_structure()