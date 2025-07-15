import requests
from bs4 import BeautifulSoup

# Analyze JRSSB paper structure for Published date and Section
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

# Analyze first few articles for Published date and Section
article_containers = soup.select('.al-article-items')
print(f'Found {len(article_containers)} containers')

for i, container in enumerate(article_containers[1:4]):  # Skip correction, check first 3
    print(f'\n=== Article {i+1} ===')
    
    # Title
    title_elem = container.select_one('.al-title a')
    if title_elem:
        print(f'Title: {title_elem.get_text(strip=True)}')
    
    print('Full container HTML:')
    container_html = str(container)
    print(container_html[:2000] + '...' if len(container_html) > 2000 else container_html)
    
    print('\n--- Looking for Published date and Section ---')
    
    # Look for all text containing "Published"
    if 'Published:' in container_html:
        print('Found "Published:" in HTML')
        # Try to extract it
        published_match = container_html.find('Published:')
        if published_match != -1:
            # Get surrounding text
            start = max(0, published_match - 100)
            end = min(len(container_html), published_match + 200)
            surrounding = container_html[start:end]
            print(f'Surrounding text: {surrounding}')
    
    # Look for Section information
    if 'Section:' in container_html:
        print('Found "Section:" in HTML')
        section_match = container_html.find('Section:')
        if section_match != -1:
            start = max(0, section_match - 50)
            end = min(len(container_html), section_match + 150)
            surrounding = container_html[start:end]
            print(f'Section surrounding: {surrounding}')
    
    # Check for "Original Article" or other section types
    if 'Original Article' in container_html:
        print('Found "Original Article" text')
    
    # Look for citation-date-wrap or other date containers
    date_wraps = container.select('.citation-date-wrap, .ww-citation-date-wrap')
    if date_wraps:
        print(f'Found {len(date_wraps)} date wrap elements:')
        for wrap in date_wraps:
            print(f'  Date wrap: {str(wrap)}')
    
    # Look for al-article-pubinfo
    pubinfo = container.select('.al-article-pubinfo')
    if pubinfo:
        print(f'Found {len(pubinfo)} pubinfo elements:')
        for info in pubinfo:
            print(f'  Pubinfo: {str(info)}')
    
    print('-' * 50)