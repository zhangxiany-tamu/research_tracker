#!/usr/bin/env python3
"""
Create comprehensive database backup
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Paper, Journal
from app.scrapers import JASAScraper, JRSSBScraper, BiometrikaScraper, AOSScraper, JMLRScraper
from app.data_service import DataService

def create_backup(description="Manual backup"):
    """Create comprehensive database backup"""
    print('📦 Creating comprehensive database backup...')
    
    # Create fresh database
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    data_service = DataService(db)
    
    scrapers = {
        'JASA': JASAScraper(),
        'JRSSB': JRSSBScraper(), 
        'Biometrika': BiometrikaScraper(),
        'AOS': AOSScraper(),
        'JMLR': JMLRScraper()
    }
    
    total_papers = 0
    results = {}
    
    try:
        for journal_name, scraper in scrapers.items():
            try:
                print(f'📰 Scraping {journal_name}...')
                papers = scraper.scrape_papers()
                
                saved_count = 0
                for paper_data in papers:
                    success = data_service.save_paper(paper_data)
                    if success:
                        saved_count += 1
                
                total_papers += saved_count
                results[journal_name] = {'found': len(papers), 'saved': saved_count}
                print(f'✅ {journal_name}: {saved_count}/{len(papers)} papers')
                
            except Exception as e:
                print(f'❌ Error scraping {journal_name}: {e}')
                results[journal_name] = {'error': str(e)}
        
        print(f'📊 BACKUP COMPLETE: {total_papers} total papers saved')
        
        # Create backup metadata
        backup_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_papers': total_papers,
            'results': results,
            'description': description
        }
        
        with open('backup_info.json', 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        print('✅ Backup database ready for upload')
        return True
        
    finally:
        db.close()

if __name__ == "__main__":
    description = sys.argv[1] if len(sys.argv) > 1 else "Manual backup"
    create_backup(description)