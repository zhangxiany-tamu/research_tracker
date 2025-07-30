#!/usr/bin/env python3
"""
Sync API endpoint to receive complete paper data and update cloud database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Paper, Journal, Author, Topic
from app.data_service import DataService
from typing import List, Dict
from datetime import datetime
import logging

router = APIRouter()

@router.post("/api/sync-papers")
async def sync_papers(papers_data: List[Dict], db: Session = Depends(get_db)):
    """
    Systematic sync endpoint to receive complete paper data
    This allows us to sync the cloud database with local/correct data
    """
    try:
        data_service = DataService(db)
        
        synced_count = 0
        updated_count = 0
        
        for paper_data in papers_data:
            try:
                # Ensure journal exists
                journal_name = paper_data.get('journal')
                if not journal_name:
                    continue
                
                journal = db.query(Journal).filter(Journal.name == journal_name).first()
                if not journal:
                    continue
                
                # Check if paper already exists
                existing_paper = db.query(Paper).filter(
                    Paper.title == paper_data.get('title'),
                    Paper.journal_id == journal.id
                ).first()
                
                if existing_paper:
                    # Update existing paper if needed
                    if paper_data.get('publication_date'):
                        try:
                            pub_date = datetime.fromisoformat(paper_data['publication_date'])
                            if existing_paper.publication_date != pub_date:
                                existing_paper.publication_date = pub_date
                                updated_count += 1
                        except:
                            pass
                    continue
                
                # Create new paper
                pub_date = None
                if paper_data.get('publication_date'):
                    try:
                        pub_date = datetime.fromisoformat(paper_data['publication_date'])
                    except:
                        pass
                
                scraped_date = datetime.now()
                if paper_data.get('scraped_date'):
                    try:
                        scraped_date = datetime.fromisoformat(paper_data['scraped_date'])
                    except:
                        pass
                
                paper = Paper(
                    title=paper_data.get('title'),
                    abstract=paper_data.get('abstract'),
                    doi=paper_data.get('doi'),
                    url=paper_data.get('url'),
                    publication_date=pub_date,
                    scraped_date=scraped_date,
                    section=paper_data.get('section'),
                    journal_id=journal.id
                )
                
                db.add(paper)
                db.flush()
                
                # Add authors
                authors = paper_data.get('authors', [])
                for author_name in authors:
                    if author_name:
                        author = data_service.get_or_create_author(author_name)
                        paper.authors.append(author)
                
                # Add topics
                detected_topics = data_service.extract_topics_from_title(paper_data.get('title', ''))
                for topic_name in detected_topics:
                    topic = data_service.get_or_create_topic(topic_name)
                    paper.topics.append(topic)
                
                synced_count += 1
                
            except Exception as e:
                logging.error(f"Error syncing paper {paper_data.get('title', 'Unknown')}: {e}")
                continue
        
        db.commit()
        
        return {
            'status': 'success',
            'synced_papers': synced_count,
            'updated_papers': updated_count,
            'total_processed': len(papers_data)
        }
        
    except Exception as e:
        db.rollback()
        logging.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.get("/api/database-stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """Get current database statistics"""
    try:
        journal_stats = {}
        
        journals = db.query(Journal).all()
        for journal in journals:
            paper_count = db.query(Paper).filter(Paper.journal_id == journal.id).count()
            journal_stats[journal.name] = paper_count
        
        total_papers = sum(journal_stats.values())
        
        return {
            'total_papers': total_papers,
            'journal_stats': journal_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")