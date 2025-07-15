import requests
from bs4 import BeautifulSoup
import re

# Test JRSSB author extraction fix
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

# Test the exact fix for author extraction
container = soup.select('.al-article-items')[1]  # Skip correction
title_elem = container.select_one('.al-title a')
print(f'Title: {title_elem.get_text(strip=True)}')

authors_elem = container.select_one('.al-authors-list')
if authors_elem:
    print(f'Original HTML: {str(authors_elem)}')
    print(f'Original text: "{authors_elem.get_text(strip=True)}"')
    
    # Apply the same fix as in the scraper
    temp_soup = BeautifulSoup(str(authors_elem), 'html.parser')
    for delim_span in temp_soup.find_all('span', class_='al-author-delim'):
        print(f'Found delimiter span: {delim_span}')
        delim_span.replace_with(' and ')  # Replace with spaced "and"
    
    authors_text = temp_soup.get_text(strip=True)
    print(f'After replacement: "{authors_text}"')
    
    # Now split by "and" with proper spacing
    author_parts = re.split(r'\s+and\s+', authors_text)
    authors = [name.strip() for name in author_parts if name.strip()]
    print(f'Final authors: {authors}')
    
    # Also test a simpler approach
    print('\nSimpler approach:')
    # Just replace the delimiter span with ' and ' in the original text
    html_with_spaces = str(authors_elem).replace('<span class="al-author-delim">and</span>', ' and ')
    simple_soup = BeautifulSoup(html_with_spaces, 'html.parser')
    simple_text = simple_soup.get_text(strip=True)
    simple_parts = re.split(r'\s+and\s+', simple_text)
    simple_authors = [name.strip() for name in simple_parts if name.strip()]
    print(f'Simple approach result: {simple_authors}')