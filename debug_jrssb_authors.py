import requests
from bs4 import BeautifulSoup

# Debug the specific author parsing issue
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

# Look for cases where we have problematic author parsing
containers = soup.select('.al-article-items')
print(f'Found {len(containers)} containers')

for i, container in enumerate(containers[:10]):  # Check first 10
    title_elem = container.select_one('.al-title a')
    if title_elem:
        title = title_elem.get_text(strip=True)
        
        authors_elem = container.select_one('.al-authors-list')
        if authors_elem:
            # Check the original HTML
            original_html = str(authors_elem)
            original_text = authors_elem.get_text(strip=True)
            
            # Apply our current fix
            authors_html = original_html.replace('<span class="al-author-delim">and</span>', ' and ')
            temp_soup = BeautifulSoup(authors_html, 'html.parser')
            fixed_text = temp_soup.get_text(strip=True)
            
            # Check if there are issues
            if 'and' in original_text and ' and ' not in fixed_text:
                print(f'\n=== PROBLEMATIC CASE {i+1} ===')
                print(f'Title: {title}')
                print(f'Original HTML: {original_html}')
                print(f'Original text: "{original_text}"')
                print(f'Fixed HTML: {authors_html}')
                print(f'Fixed text: "{fixed_text}"')
                
                # Test split
                import re
                author_parts = re.split(r'\s+and\s+', fixed_text)
                print(f'Split result: {author_parts}')
                
                # Also check for other patterns
                if 'and others' in original_text:
                    print('*** Contains "and others" pattern ***')
                if 'et al' in original_text:
                    print('*** Contains "et al" pattern ***')