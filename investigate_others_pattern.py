import requests
from bs4 import BeautifulSoup

# Investigate different patterns for "others" in JRSSB
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

# Look for all "others" patterns
containers = soup.select('.al-article-items')
print(f'Found {len(containers)} containers')
print()

others_patterns = []
for i, container in enumerate(containers):
    title_elem = container.select_one('.al-title a')
    if title_elem:
        title = title_elem.get_text(strip=True)
        
        authors_elem = container.select_one('.al-authors-list')
        if authors_elem and 'others' in authors_elem.get_text():
            original_html = str(authors_elem)
            original_text = authors_elem.get_text(strip=True)
            
            print(f'=== CASE {i+1}: "others" pattern ===')
            print(f'Title: {title}')
            print(f'Original HTML: {original_html}')
            print(f'Original text: "{original_text}"')
            
            # Apply current fix
            authors_html = original_html
            authors_html = authors_html.replace('<span class="al-author-delim">and</span>', ' and ')
            authors_html = authors_html.replace('<span class="al-author-delim">and others</span>', ' and others')
            
            temp_soup = BeautifulSoup(authors_html, 'html.parser')
            fixed_text = temp_soup.get_text(strip=True)
            print(f'Fixed text: "{fixed_text}"')
            
            # Test split
            import re
            author_parts = re.split(r'\s+and\s+', fixed_text)
            print(f'Split result: {author_parts}')
            
            others_patterns.append({
                'title': title,
                'original_html': original_html,
                'original_text': original_text,
                'fixed_text': fixed_text,
                'split_result': author_parts
            })
            print()

print(f'Found {len(others_patterns)} papers with "others" pattern')
print()
print('Summary of patterns:')
for i, pattern in enumerate(others_patterns, 1):
    print(f'{i}. {pattern["title"][:50]}... -> {pattern["split_result"]}')