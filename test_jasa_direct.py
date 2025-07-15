#!/usr/bin/env python3
"""
Test script to try different approaches to access JASA papers
"""

import requests
from bs4 import BeautifulSoup
import time
import json

def test_jasa_access():
    print("Testing JASA Direct Access...")
    print("=" * 60)
    
    # Try different session configurations
    session = requests.Session()
    
    # Test 1: Basic access with minimal headers
    print("\n1. Testing basic access...")
    try:
        response = session.get("https://www.tandfonline.com/action/showAxaArticles?journalCode=uasa20&startPage=0")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Basic access successful!")
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"   Page title: {soup.title.string if soup.title else 'No title'}")
        else:
            print(f"   ✗ Basic access failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Basic access error: {e}")
    
    # Test 2: Try with different headers
    print("\n2. Testing with browser headers...")
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
    
    try:
        response = session.get("https://www.tandfonline.com/action/showAxaArticles?journalCode=uasa20&startPage=0")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Browser headers successful!")
            soup = BeautifulSoup(response.content, 'html.parser')
            # Look for articles
            articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('article' in x.lower() or 'result' in x.lower()))
            print(f"   Found {len(articles)} potential article elements")
            return soup
        else:
            print(f"   ✗ Browser headers failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Browser headers error: {e}")
    
    # Test 3: Try accessing the main journal page first
    print("\n3. Testing main journal page first...")
    try:
        main_response = session.get("https://www.tandfonline.com/loi/uasa20")
        print(f"   Main page status: {main_response.status_code}")
        if main_response.status_code == 200:
            time.sleep(2)  # Wait before accessing advance articles
            response = session.get("https://www.tandfonline.com/action/showAxaArticles?journalCode=uasa20&startPage=0")
            print(f"   Advance articles status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Sequential access successful!")
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup
    except Exception as e:
        print(f"   ✗ Sequential access error: {e}")
    
    # Test 4: Try with a longer delay and cookies
    print("\n4. Testing with session persistence...")
    try:
        # First visit the main site
        session.get("https://www.tandfonline.com/")
        time.sleep(3)
        
        # Then try the advance articles
        response = session.get("https://www.tandfonline.com/action/showAxaArticles?journalCode=uasa20&startPage=0")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ Session persistence successful!")
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
    except Exception as e:
        print(f"   ✗ Session persistence error: {e}")
    
    print("\n" + "=" * 60)
    print("All access methods failed - site is likely blocking automated access")
    return None

def analyze_page_structure(soup):
    """Analyze the page structure if we get access"""
    print("\nAnalyzing page structure...")
    
    # Look for different types of content containers
    selectors_to_try = [
        'article',
        '.article',
        '.searchResult',
        '.citation',
        '.hlFld-Title',
        '.art_title',
        '[class*="article"]',
        '[class*="result"]',
        '[class*="title"]',
        'h2', 'h3', 'h4'
    ]
    
    for selector in selectors_to_try:
        elements = soup.select(selector)
        if elements:
            print(f"   Found {len(elements)} elements with selector: {selector}")
            if len(elements) > 0:
                print(f"   Sample text: {elements[0].get_text()[:100]}...")

if __name__ == "__main__":
    soup = test_jasa_access()
    if soup:
        analyze_page_structure(soup)
    else:
        print("\nCould not access page for analysis")