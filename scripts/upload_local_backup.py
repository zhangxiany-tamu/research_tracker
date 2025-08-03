#!/usr/bin/env python3
"""
Upload local database as GitHub artifact
"""

import os
import sys
import json
import shutil
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Paper, Journal

def create_local_backup():
    """Create backup info from existing local database"""
    
    if not os.path.exists('research_tracker.db'):
        print("❌ Local database file not found!")
        return False
    
    # Copy the existing database for backup
    if os.path.exists('local_backup_research_tracker.db'):
        shutil.copy('local_backup_research_tracker.db', 'research_tracker.db')
        print("📦 Using committed local database backup")
    else:
        print("⚠️ No local backup found, using current database")
    
    # Create backup copy for artifact
    shutil.copy('research_tracker.db', 'backup_research_tracker.db')
    print("📦 Prepared database for backup")
    
    # Get stats from existing database
    db = SessionLocal()
    try:
        total_papers = db.query(Paper).count()
        
        # Get papers by journal
        journal_stats = {}
        journals = db.query(Journal).all()
        for journal in journals:
            paper_count = db.query(Paper).filter(Paper.journal_id == journal.id).count()
            journal_stats[journal.name] = paper_count
            print(f"  {journal.name}: {paper_count} papers")
        
        print(f"📊 Total papers in local database: {total_papers}")
        
        # Create backup metadata
        backup_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_papers': total_papers,
            'journal_stats': journal_stats,
            'description': 'Local database backup with all existing papers',
            'source': 'local_existing_database'
        }
        
        with open('backup_info.json', 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        print('✅ Backup metadata created')
        return True
        
    except Exception as e:
        print(f"❌ Error reading local database: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = create_local_backup()
    if not success:
        sys.exit(1)