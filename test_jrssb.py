import requests
from bs4 import BeautifulSoup

# Deeper analysis of JRSSB structure
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

# Find article containers
article_containers = soup.select('.al-article-items')
print(f'Found {len(article_containers)} article containers')

if article_containers:
    print()
    print('--- Analyzing article container structure ---')
    container = article_containers[1]  # Skip the first one (correction)
    
    # Extract all relevant information
    print('Full container HTML:')
    print(str(container)[:1000] + '...')
    
    print()
    print('--- Extracting data ---')
    
    # Title
    title_elem = container.select_one('.al-title a')
    if title_elem:
        title = title_elem.get_text(strip=True)
        url = title_elem.get('href')
        print(f'Title: {title}')
        print(f'URL: https://academic.oup.com{url}')
    
    # Authors
    author_elements = container.select('[class*="author"]')
    authors = []
    for elem in author_elements:
        text = elem.get_text(strip=True)
        if text and text != 'and':
            authors.append(text)
    print(f'Authors: {authors}')
    
    # Date
    date_elem = container.select_one('.al-pub-date')
    if date_elem:
        date_text = date_elem.get_text(strip=True)
        print(f'Date: {date_text}')
    
    # Type  
    type_elem = container.select_one('.sri-type')
    if type_elem:
        type_text = type_elem.get_text(strip=True)
        print(f'Type: {type_text}')