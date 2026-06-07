#!/usr/bin/env python3
"""
Sync API endpoint to receive complete paper data and update cloud database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Paper, Journal
from app.data_service import DataService
from typing import List, Dict
from datetime import datetime
import logging

router = APIRouter()
SYNC_COMMIT_INTERVAL = 25


def parse_optional_datetime(value):
    """Parse an ISO datetime value from scraper JSON."""
    if not value:
        return None

    try:
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    except (TypeError, ValueError):
        return None

@router.post("/api/sync-papers")
async def sync_papers(papers_data: List[Dict], db: Session = Depends(get_db)):
    """
    Systematic sync endpoint to receive complete paper data
    This allows us to sync the cloud database with local/correct data
    """
    try:
        data_service = DataService(db)
        journals_by_name = {journal.name: journal for journal in db.query(Journal).all()}

        synced_count = 0
        updated_count = 0
        skipped_count = 0
        pending_writes = 0

        for paper_data in papers_data:
            try:
                # Ensure journal exists
                journal_name = paper_data.get('journal')
                title = paper_data.get('title')
                if not journal_name or not title:
                    skipped_count += 1
                    continue

                journal = journals_by_name.get(journal_name)
                if not journal:
                    logging.warning(f"Skipping paper with unknown journal '{journal_name}': {title}")
                    skipped_count += 1
                    continue

                paper_action = None

                with db.begin_nested():
                    # Check if paper already exists (multiple criteria for robust duplicate detection)
                    existing_paper = None

                    # First check by DOI if available (most reliable)
                    doi = paper_data.get('doi')
                    if doi:
                        existing_paper = db.query(Paper).filter(Paper.doi == doi).first()

                    # If no DOI match, check by title + journal (fallback)
                    if not existing_paper:
                        existing_paper = db.query(Paper).filter(
                            Paper.title == title,
                            Paper.journal_id == journal.id
                        ).first()

                    if existing_paper:
                        # Update existing paper if needed
                        updated = False

                        # Update publication date if available
                        pub_date = parse_optional_datetime(paper_data.get('publication_date'))
                        if pub_date:
                            if existing_paper.publication_date != pub_date:
                                existing_paper.publication_date = pub_date
                                updated = True

                        # Update DOI if existing paper doesn't have one but new data does
                        if doi and not existing_paper.doi:
                            existing_paper.doi = doi
                            updated = True

                        # Update URL if existing paper doesn't have one but new data does
                        new_url = paper_data.get('url')
                        if new_url and not existing_paper.url:
                            existing_paper.url = new_url
                            updated = True

                        if updated:
                            paper_action = "updated"

                    else:
                        pub_date = parse_optional_datetime(paper_data.get('publication_date'))
                        scraped_date = parse_optional_datetime(paper_data.get('scraped_date')) or datetime.now()

                        # Create new paper
                        paper = Paper(
                            title=title,
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
                            if author_name and author_name.strip():
                                author = data_service.get_or_create_author(author_name.strip())
                                paper.authors.append(author)

                        # Add topics
                        detected_topics = data_service.extract_topics_from_title(title)
                        for topic_name in detected_topics:
                            topic = data_service.get_or_create_topic(topic_name)
                            paper.topics.append(topic)

                        paper_action = "synced"

                if paper_action == "updated":
                    updated_count += 1
                    pending_writes += 1
                elif paper_action == "synced":
                    synced_count += 1
                    pending_writes += 1

                if pending_writes >= SYNC_COMMIT_INTERVAL:
                    db.commit()
                    pending_writes = 0

            except IntegrityError as paper_error:
                skipped_count += 1
                logging.warning(
                    f"Skipping paper with integrity error '{paper_data.get('title', 'Unknown')}': {paper_error}"
                )
                continue
            except OperationalError:
                db.rollback()
                logging.exception(f"Database connection failed while syncing '{paper_data.get('title', 'Unknown')}'")
                raise
            except SQLAlchemyError as paper_error:
                skipped_count += 1
                logging.error(
                    f"Skipping paper with database error '{paper_data.get('title', 'Unknown')}': {paper_error}"
                )
                continue
            except Exception as e:
                logging.error(f"Error syncing paper {paper_data.get('title', 'Unknown')}: {e}")
                skipped_count += 1
                continue

        db.commit()

        return {
            'status': 'success',
            'synced_papers': synced_count,
            'updated_papers': updated_count,
            'skipped_papers': skipped_count,
            'total_processed': len(papers_data)
        }

    except OperationalError as e:
        db.rollback()
        logging.error(f"Sync database connection error: {e}")
        raise HTTPException(status_code=503, detail=f"Sync database connection failed: {str(e)}")
    except Exception as e:
        db.rollback()
        logging.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/api/update-journals")
async def update_journals(db: Session = Depends(get_db)):
    """Update existing journals with abbreviations"""
    try:
        journal_updates = [
            {"name": "Annals of Statistics", "abbreviation": "AOS"},
            {"name": "Journal of Machine Learning Research", "abbreviation": "JMLR"},
            {"name": "Journal of the American Statistical Association", "abbreviation": "JASA"},
            {"name": "Journal of the Royal Statistical Society Series B", "abbreviation": "JRSSB"},
            {"name": "Biometrika", "abbreviation": "Biometrika"}
        ]

        updated_count = 0
        for update_data in journal_updates:
            journal = db.query(Journal).filter(Journal.name == update_data["name"]).first()
            if journal:
                journal.abbreviation = update_data["abbreviation"]
                updated_count += 1

        db.commit()

        return {
            'status': 'success',
            'updated_journals': updated_count,
            'message': f'Updated {updated_count} journals with abbreviations'
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Journal update failed: {str(e)}")

@router.post("/api/init-journals")
async def init_journals(db: Session = Depends(get_db)):
    """Initialize missing journals in the database"""
    try:
        journals_data = [
            {"name": "Annals of Statistics", "short_name": "AOS", "abbreviation": "AOS", "url": "https://imstat.org/journals-and-publications/annals-of-statistics/"},
            {"name": "Journal of Machine Learning Research", "short_name": "JMLR", "abbreviation": "JMLR", "url": "https://www.jmlr.org/"},
            {"name": "Journal of the American Statistical Association", "short_name": "JASA", "abbreviation": "JASA", "url": "https://www.tandfonline.com/toc/uasa20/current"},
            {"name": "Journal of the Royal Statistical Society Series B", "short_name": "JRSS-B", "abbreviation": "JRSS-B", "url": "https://academic.oup.com/jrsssb"},
            {"name": "Biometrika", "short_name": "Biometrika", "abbreviation": "Biometrika", "url": "https://academic.oup.com/biomet"}
        ]

        created_count = 0
        for journal_data in journals_data:
            existing_journal = db.query(Journal).filter(Journal.name == journal_data["name"]).first()
            if not existing_journal:
                journal = Journal(**journal_data)
                db.add(journal)
                created_count += 1
                logging.info(f"Created journal: {journal_data['name']}")

        db.commit()

        return {
            'status': 'success',
            'created_journals': created_count,
            'message': f'Initialized {created_count} missing journals'
        }

    except Exception as e:
        db.rollback()
        logging.error(f"Journal initialization error: {e}")
        raise HTTPException(status_code=500, detail=f"Journal initialization failed: {str(e)}")

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
