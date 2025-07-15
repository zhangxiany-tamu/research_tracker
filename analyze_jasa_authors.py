#!/usr/bin/env python3
"""
Analyze JASA page structure to find author information
"""

import requests
from bs4 import BeautifulSoup
import time

def analyze_jasa_authors():
    print("Analyzing JASA Author Extraction...")
    print("=" * 50)
    
    session = requests.Session()
    session.headers.update({
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
    
    # Test the advance articles page where we're getting papers from
    try:
        response = session.get("https://www.tandfonline.com/action/showAxaArticles?journalCode=uasa20&startPage=0")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find title elements
            titles = soup.select('.hlFld-Title')
            print(f"Found {len(titles)} title elements")
            
            # Debug: Let's see what's in the title elements
            print("Sample title elements:")
            for i, title_elem in enumerate(titles[:3]):
                print(f"Title {i}: {title_elem}")
                print(f"Title text: '{title_elem.get_text(strip=True)}'")
                print(f"Title HTML: {str(title_elem)[:200]}")
                print("-" * 20)
                
            # Analyze the first few papers
            for i, title_elem in enumerate(titles[:3]):
                print(f"\n--- Paper {i+1} ---")
                title = title_elem.get_text(strip=True)
                print(f"Title: {title}")
                
                # Look for authors near the title
                # Check parent elements and siblings
                parent = title_elem.parent
                if parent:
                    print(f"Parent tag: {parent.name}")
                    print(f"Parent classes: {parent.get('class', [])}")
                    
                    # Print some context around the title
                    print(f"Parent HTML snippet:")
                    print(str(parent)[:500] + "...")
                    
                    # Look for author-related elements in a wider search
                    row_container = title_elem.find_parent('tr')  # Table row
                    if row_container:
                        print("Found table row container")
                        cells = row_container.find_all('td')
                        for j, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            print(f"  Cell {j}: {cell_text[:100]}")
                            
                            # Check if this cell contains author information
                            if any(keyword in cell_text.lower() for keyword in ['author', 'by ']):
                                print(f"    -> Potential author cell!")
                    
                    # Look for author-related elements
                    author_selectors = [
                        '.hlFld-ContribAuthor',
                        '.entryAuthor', 
                        '.author',
                        '.authors',
                        '.contrib-author',
                        '[class*="author"]',
                        '[class*="Author"]'
                    ]
                    
                    # Search in a wider scope - go up to find the article container
                    # Look for a container that might have both title and author info
                    broader_scope = title_elem.find_parent(['div', 'tr', 'article', 'li'])
                    while broader_scope and broader_scope.name != 'body':
                        # Check if this container has author information
                        container_text = broader_scope.get_text()
                        if len(container_text) > len(title) * 2:  # Container has more than just title
                            print(f"Checking container: {broader_scope.name} with classes {broader_scope.get('class', [])}")
                            print(f"Container text: {container_text[:200]}...")
                            
                            # Look for author elements in this container
                            for selector in author_selectors:
                                authors = broader_scope.select(selector)
                                if authors:
                                    print(f"Found authors with selector '{selector}':")
                                    for author in authors:
                                        author_text = author.get_text(strip=True)
                                        print(f"  - {author_text}")
                                        
                            # Look for specific author patterns
                            if any(pattern in container_text.lower() for pattern in ['by ', 'author']):
                                print("Found author pattern in container!")
                                
                            # Also check siblings of the title container
                            if broader_scope.name == 'tr':
                                # Table row - check cells
                                cells = broader_scope.find_all('td')
                                for j, cell in enumerate(cells):
                                    cell_text = cell.get_text(strip=True)
                                    print(f"  Cell {j}: {cell_text[:100]}")
                                    if cell_text != title and any(keyword in cell_text.lower() for keyword in ['author', 'by ']):
                                        print(f"    -> Potential author cell: {cell_text}")
                            
                            break
                        broader_scope = broader_scope.parent
                    
                    # Final attempt - look for elements with "ContribAuthor" class
                    contrib_authors = soup.select('.hlFld-ContribAuthor')
                    if contrib_authors:
                        print(f"Found {len(contrib_authors)} contrib author elements on page")
                        for author_elem in contrib_authors[:5]:  # Show first 5
                            print(f"  Contrib author: {author_elem.get_text(strip=True)}")
                
                print("-" * 30)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_jasa_authors()