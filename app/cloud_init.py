#!/usr/bin/env python3
"""
Cloud database initialization script
Ensures cloud database is populated with journal data and current papers
"""

import os
import json
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import Base, Journal, Paper, Author, Topic
from app.data_service import DataService
from datetime import datetime

def init_journals(db: Session):
    """Initialize the journals table"""
    journals_data = [
        {"name": "Annals of Statistics", "short_name": "AOS", "url": "https://imstat.org/journals-and-publications/annals-of-statistics/"},
        {"name": "Journal of Machine Learning Research", "short_name": "JMLR", "url": "https://www.jmlr.org/"},
        {"name": "Journal of the American Statistical Association", "short_name": "JASA", "url": "https://www.tandfonline.com/toc/uasa20/current"},
        {"name": "Journal of the Royal Statistical Society Series B", "short_name": "JRSS-B", "url": "https://academic.oup.com/jrsssb"},
        {"name": "Biometrika", "short_name": "Biometrika", "url": "https://academic.oup.com/biomet"}
    ]
    
    for journal_data in journals_data:
        existing_journal = db.query(Journal).filter(Journal.name == journal_data["name"]).first()
        if not existing_journal:
            journal = Journal(**journal_data)
            db.add(journal)
            print(f"Added journal: {journal_data['name']}")
    
    try:
        db.commit()
        print("✅ Journals initialized successfully")
    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing journals: {e}")
        raise

def init_cloud_database():
    """Initialize cloud database with tables and journals"""
    print("🔧 Initializing cloud database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
        
        # Initialize journals
        db = SessionLocal()
        try:
            init_journals(db)
        finally:
            db.close()
        
        print("✅ Cloud database initialization complete")
        return True
        
    except Exception as e:
        print(f"❌ Cloud database initialization failed: {e}")
        return False

def get_database_stats():
    """Get current database statistics"""
    try:
        db = SessionLocal()
        try:
            journal_stats = {}
            journals = db.query(Journal).all()
            
            for journal in journals:
                paper_count = db.query(Paper).filter(Paper.journal_id == journal.id).count()
                journal_stats[journal.name] = paper_count
            
            total_papers = sum(journal_stats.values())
            
            return {
                'total_papers': total_papers,
                'journal_stats': journal_stats,
                'status': 'success'
            }
        finally:
            db.close()
            
    except Exception as e:
        return {
            'total_papers': 0,
            'journal_stats': {},
            'status': 'error',
            'error': str(e)
        }

if __name__ == "__main__":
    # Initialize database when run directly
    success = init_cloud_database()
    if success:
        stats = get_database_stats()
        print(f"📊 Database stats: {stats}")
    else:
        exit(1)