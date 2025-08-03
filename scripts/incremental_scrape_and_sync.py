#!/usr/bin/env python3
"""
Incremental scraping script - only fetches recent papers (last 60 days)
Much more efficient than full scraping for daily updates
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime, date, timedelta
from app.database import SessionLocal, create_tables
from app.scrapers import JASAScraper, JRSSBScraper, BiometrikaScraper, AOSScraper, JMLRScraper
from app.data_service import DataService

class IncrementalScrapers:
    """Enhanced scrapers that only fetch recent papers"""
    
    @staticmethod
    def get_recent_cutoff_date(days_back=60):
        """Get cutoff date for recent papers (default: last 60 days)"""
        return datetime.now() - timedelta(days=days_back)
    
    @staticmethod
    def is_paper_recent(paper_data, cutoff_date):
        """Check if paper is recent based on publication or scraped date"""
        pub_date = paper_data.get('publication_date')
        scraped_date = paper_data.get('scraped_date') 
        
        # If we have publication date, use that
        if pub_date:
            if isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                except:
                    pub_date = None
            if pub_date and pub_date >= cutoff_date:
                return True
        
        # Fallback to scraped date
        if scraped_date:
            if isinstance(scraped_date, str):
                try:
                    scraped_date = datetime.fromisoformat(scraped_date.replace('Z', '+00:00'))
                except:
                    scraped_date = None
            if scraped_date and scraped_date >= cutoff_date:
                return True
        
        # If no dates available, assume recent (safety fallback)
        return True

def main():
    print("🔄 INCREMENTAL RESEARCH TRACKER - RECENT PAPERS ONLY")
    print("=" * 60)
    
    # Setup
    create_tables()
    cutoff_date = IncrementalScrapers.get_recent_cutoff_date(days_back=60)
    print(f"📅 Fetching papers newer than: {cutoff_date.strftime('%Y-%m-%d')}")
    
    db = SessionLocal()
    data_service = DataService(db)
    
    # Enhanced scrapers with recent-only logic
    scrapers_config = {
        'JASA': {
            'scraper': JASAScraper(),
            'recent_pages_only': True,  # Already optimized to pages 0-2
            'max_pages': 2  # Only first 2 pages for recent papers
        },
        'JRSSB': {
            'scraper': JRSSBScraper(),
            'recent_pages_only': True,  # Advance articles are naturally recent
            'max_pages': 1
        },
        'Biometrika': {
            'scraper': BiometrikaScraper(),
            'recent_pages_only': True,  # Advance articles are naturally recent  
            'max_pages': 1
        },
        'AOS': {
            'scraper': AOSScraper(),
            'recent_pages_only': True,  # Future papers are naturally recent
            'max_pages': 1
        },
        'JMLR': {
            'scraper': JMLRScraper(),
            'recent_pages_only': True,  # Latest papers section is naturally recent
            'max_pages': 1
        }
    }
    
    all_papers_data = []
    results = {}
    
    for journal_name, config in scrapers_config.items():
        try:
            print(f"\n📰 Scraping {journal_name} (recent papers only)...")
            scraper = config['scraper']
            
            # Get papers
            papers = scraper.scrape_papers()
            print(f"Found {len(papers)} papers from {journal_name}")
            
            # Filter for recent papers only
            recent_papers = []
            for paper in papers:
                if IncrementalScrapers.is_paper_recent(paper, cutoff_date):
                    recent_papers.append(paper)
            
            print(f"Filtered to {len(recent_papers)} recent papers (last 60 days)")
            
            # Save locally and prepare for cloud sync
            saved_count = 0
            for paper_data in recent_papers:
                success = data_service.save_paper(paper_data)
                if success:
                    saved_count += 1
                
                # Prepare for cloud sync
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
                'total_found': len(papers),
                'recent_found': len(recent_papers),
                'saved': saved_count
            }
            
            print(f"✅ {journal_name}: {saved_count}/{len(recent_papers)} recent papers saved")
            
        except Exception as e:
            print(f"❌ Error scraping {journal_name}: {e}")
            results[journal_name] = {'error': str(e)}
    
    db.close()
    
    # Print summary
    print(f"\n📊 INCREMENTAL SCRAPING SUMMARY")
    print("=" * 40)
    total_found = sum(r.get('recent_found', 0) for r in results.values() if 'error' not in r)
    total_saved = sum(r.get('saved', 0) for r in results.values() if 'error' not in r)
    print(f"Recent papers found: {total_found}")
    print(f"Recent papers saved: {total_saved}")
    print(f"Papers for cloud sync: {len(all_papers_data)}")
    
    # Cloud sync
    cloud_url = os.getenv('CLOUD_URL', 'https://research-tracker-466018.uc.r.appspot.com')
    if all_papers_data:
        try:
            print(f"\n🌐 Syncing {len(all_papers_data)} recent papers to cloud...")
            
            response = requests.post(
                f'{cloud_url}/api/sync-papers',
                json=all_papers_data,
                headers={'Content-Type': 'application/json'},
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Incremental sync successful!")
                print(f"   🆕 New papers: {result.get('synced_papers', 0)}")
                print(f"   🔄 Updated papers: {result.get('updated_papers', 0)}")
                print(f"   📊 Total processed: {result.get('total_processed', 0)}")
                
                # Show efficiency gain
                sync_efficiency = result.get('synced_papers', 0) / len(all_papers_data) * 100 if all_papers_data else 0
                print(f"   📈 Sync efficiency: {sync_efficiency:.1f}% (new/processed)")
                
            else:
                print(f"❌ Cloud sync failed: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except Exception as e:
            print(f"❌ Cloud sync error: {e}")
    else:
        print("📝 No recent papers to sync")
    
    print(f"\n🎉 INCREMENTAL SYNC COMPLETED!")
    print(f"⚡ Much more efficient than full scraping!")

if __name__ == "__main__":
    main()