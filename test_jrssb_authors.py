import requests
from bs4 import BeautifulSoup
import re

# Test JRSSB author extraction specifically
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
    'Referer': 'https://academic.oup.com/'
})

response = session.get('https://academic.oup.com/jrsssb/advance-articles', timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

# Test author extraction
article_containers = soup.select('.al-article-items')
print(f'Found {len(article_containers)} containers')

for i, container in enumerate(article_containers[1:4]):  # Test first 3 (skip correction)
    print(f'\n=== Article {i+1} ===')
    
    # Title
    title_elem = container.select_one('.al-title a')
    if title_elem:
        print(f'Title: {title_elem.get_text(strip=True)}')
    
    # Authors - test different approaches
    authors_elem = container.select_one('.al-authors-list')
    if authors_elem:
        authors_html = str(authors_elem)
        authors_text = authors_elem.get_text(strip=True)
        print(f'Authors HTML: {authors_html}')
        print(f'Authors text: "{authors_text}"')
        
        # Try different splitting approaches
        print('Splitting approaches:')
        
        # Approach 1: Split by "and"
        split1 = re.split(r'\s+and\s+', authors_text)
        print(f'  Split by "and": {split1}')
        
        # Approach 2: Look for spans or elements
        author_spans = authors_elem.find_all(['span', 'a'])
        if author_spans:
            span_texts = [span.get_text(strip=True) for span in author_spans if span.get_text(strip=True) != 'and']
            print(f'  From spans: {span_texts}')
        
        # Approach 3: Remove "and" spans and split remaining text
        # Clone the element to avoid modifying original
        temp_elem = BeautifulSoup(str(authors_elem), 'html.parser')
        for span in temp_elem.find_all('span', class_='al-author-delim'):
            span.decompose()
        clean_text = temp_elem.get_text(strip=True)
        print(f'  After removing delim spans: "{clean_text}"')
        
    else:
        print('No authors element found')