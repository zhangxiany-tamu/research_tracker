#!/usr/bin/env python3
"""
Scrape papers locally and sync to cloud database
Can be run manually or by GitHub Actions
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Paper, Journal
from app.scrapers import JASAScraper, JRSSBScraper, BiometrikaScraper, AOSScraper, JMLRScraper
from app.data_service import DataService
from cloud_sync import sync_to_cloud

def setup_local_database():
    """Create fresh local database"""
    print("🗄️  Setting up local database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Local database ready")

def scrape_all_papers():
    """Scrape papers from all journals"""
    print("🔄 Starting comprehensive scraping...")
    
    db = SessionLocal()
    data_service = DataService(db)
    
    scrapers = {
        'JASA': JASAScraper(),
        'JRSSB': JRSSBScraper(), 
        'Biometrika': BiometrikaScraper(),
        'AOS': AOSScraper(),
        'JMLR': JMLRScraper()
    }
    
    results = {}
    all_papers_data = []
    
    try:
        for journal_name, scraper in scrapers.items():
            try:
                print(f"\n📰 Scraping {journal_name}...")
                papers = scraper.scrape_papers()
                print(f"Found {len(papers)} papers")
                
                saved_count = 0
                for paper_data in papers:
                    success = data_service.save_paper(paper_data)
                    if success:
                        saved_count += 1
                    
                    # Prepare for cloud sync (convert dates to ISO format)
                    paper_sync_data = {
                        'title': paper_data.get('title'),
                        'authors': paper_data.get('authors', []),
                        'journal': paper_data.get('journal'),
                        'url': paper_data.get('url'),
                        'doi': paper_data.get('doi'),
                        'abstract': paper_data.get('abstract'),
                        'section': paper_data.get('section'),
                        'publication_date': paper_data.get('publication_date').isoformat() if paper_data.get('publication_date') else None,
                        'scraped_date': paper_data.get('scraped_date').isoformat() if paper_data.get('scraped_date') else None
                    }
                    all_papers_data.append(paper_sync_data)
                
                results[journal_name] = {
                    'found': len(papers),
                    'saved': saved_count
                }
                
                print(f"✅ {saved_count}/{len(papers)} papers saved locally")
                
            except Exception as e:
                print(f"❌ Error scraping {journal_name}: {e}")
                results[journal_name] = {'error': str(e)}
        
        return all_papers_data, results
        
    finally:
        db.close()

def print_summary(results):
    """Print scraping summary"""
    print(f"\n{'='*60}")
    print("SCRAPING SUMMARY")
    print(f"{'='*60}")
    
    total_found = 0
    total_saved = 0
    
    for journal, result in results.items():
        if 'error' in result:
            print(f"{journal:15}: ❌ Error - {result['error']}")
        else:
            found = result.get('found', 0)
            saved = result.get('saved', 0)
            print(f"{journal:15}: {saved:3d}/{found:3d} papers")
            total_found += found
            total_saved += saved
    
    print(f"{'='*60}")
    print(f"{'Total':15}: {total_saved:3d}/{total_found:3d} papers")
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

def main():
    """Main function"""
    print("RESEARCH TRACKER - SCRAPE AND SYNC")
    print("="*60)
    
    # Step 1: Setup local database
    setup_local_database()
    
    # Step 2: Scrape all papers
    papers_data, results = scrape_all_papers()
    
    # Step 3: Print summary
    print_summary(results)
    
    # Step 4: Sync to cloud
    if papers_data:
        cloud_url = os.getenv('CLOUD_URL', '').strip()
        if not cloud_url:
            cloud_url = 'https://research-tracker-466018.uc.r.appspot.com'
        sync_success = sync_to_cloud(papers_data, cloud_url)
        
        if sync_success:
            print(f"\n🎉 SCRAPE AND SYNC COMPLETED SUCCESSFULLY!")
        else:
            print(f"\n❌ Scraping completed but cloud sync failed")
            return 1
    else:
        print(f"\n❌ No papers to sync")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
