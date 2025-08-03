from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import asyncio
from datetime import datetime, timedelta

from app.database import get_db, create_tables, SessionLocal
from app.models import Paper, Author, Journal, Topic
from app.scrapers import get_all_scrapers
from app.data_service import DataService
from app.sync_endpoint import router as sync_router
from app.cloud_init import init_cloud_database

app = FastAPI(title="Research Tracker", description="Track recent papers from statistics journals")

# Include sync router
app.include_router(sync_router)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add custom Jinja2 filter for consistent author ordering
def format_authors_filter(authors):
    """Ensure consistent author ordering with 'others' at the end"""
    if not authors:
        return []
    author_names = [author.name if hasattr(author, 'name') else str(author) for author in authors]
    if 'others' in author_names:
        # Move 'others' to the end
        author_names = [name for name in author_names if name != 'others'] + ['others']
    return author_names

templates.env.filters['format_authors'] = format_authors_filter

# Create database tables on startup
@app.on_event("startup")
def startup():
    create_tables()
    # Initialize cloud database if running on Google App Engine
    import os
    if os.getenv('GAE_ENV', '').startswith('standard'):
        print("🌐 Running on Google App Engine - initializing cloud database...")
        init_cloud_database()
        
        # Check if database is empty and auto-trigger restoration
        db = SessionLocal()
        try:
            paper_count = db.query(Paper).count()
            if paper_count == 0:
                print("⚠️ Database is empty after restart - triggering auto-restoration...")
                
                # Try to trigger database restore from backup
                try:
                    import subprocess
                    import os
                    
                    # Only trigger if we have GitHub token (in production)
                    github_token = os.getenv('GITHUB_TOKEN')
                    if github_token:
                        print("🔄 Triggering database restore from backup...")
                        result = subprocess.run([
                            'gh', 'workflow', 'run', 'Restore Database from Backup',
                            '--repo', 'zhangxiany-tamu/research_tracker'
                        ], capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            print("✅ Auto-restoration from backup triggered successfully")
                            print("📦 Database will be restored from latest backup in ~2 minutes")
                        else:
                            print(f"❌ Auto-restoration failed: {result.stderr}")
                            print("💡 Fallback: Please manually trigger 'Restore Database from Backup' workflow")
                    else:
                        print("💡 No GitHub token available - manual restoration needed")
                        print("💡 Please trigger 'Restore Database from Backup' workflow manually")
                        
                except Exception as trigger_error:
                    print(f"❌ Could not trigger auto-restoration: {trigger_error}")
                    print("💡 Please manually trigger the 'Restore Database from Backup' workflow")
                    
        except Exception as e:
            print(f"Could not check database status: {e}")
        finally:
            db.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    # Get recent papers - order by publication_date first, then scraped_date as fallback
    recent_papers = db.query(Paper).order_by(
        desc(Paper.publication_date), 
        desc(Paper.scraped_date)
    ).limit(20).all()
    
    # Get journal statistics
    journal_stats = db.query(
        Journal.name, 
        func.count(Paper.id).label('paper_count')
    ).join(Paper).group_by(Journal.id).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_papers": recent_papers,
        "journal_stats": journal_stats
    })

@app.get("/papers", response_class=HTMLResponse)
async def papers(
    request: Request, 
    journal: Optional[str] = None,
    author: Optional[str] = None,
    topic: Optional[str] = None,
    days: Optional[str] = None,
    sort: Optional[str] = "date_desc",
    db: Session = Depends(get_db)
):
    query = db.query(Paper)
    
    # Filter by journal
    if journal:
        query = query.join(Journal).filter(Journal.name == journal)
    
    # Filter by author
    if author:
        author_search = author.strip()
        # Handle both "Last, First" and "First Last" formats
        if ',' in author_search:
            # Convert "Last, First" to "First Last" format
            parts = [part.strip() for part in author_search.split(',')]
            if len(parts) == 2:
                last_name, first_name = parts
                converted_name = f"{first_name} {last_name}"
                # Search for both formats
                query = query.join(Paper.authors).filter(
                    Author.name.contains(author_search) | 
                    Author.name.contains(converted_name)
                )
            else:
                query = query.join(Paper.authors).filter(Author.name.contains(author_search))
        else:
            # For "First Last" format, also search for "Last, First"
            parts = author_search.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = ' '.join(parts[1:])
                converted_name = f"{last_name}, {first_name}"
                # Search for both formats
                query = query.join(Paper.authors).filter(
                    Author.name.contains(author_search) | 
                    Author.name.contains(converted_name)
                )
            else:
                query = query.join(Paper.authors).filter(Author.name.contains(author_search))
    
    # Filter by topic
    if topic:
        query = query.join(Paper.topics).filter(Topic.name == topic)
    
    # Filter by date
    days_int = None
    if days and days.strip():
        try:
            days_int = int(days)
            cutoff_date = datetime.utcnow() - timedelta(days=days_int)
            # Use publication_date if available, otherwise fall back to scraped_date
            query = query.filter(
                (Paper.publication_date.is_not(None) & (Paper.publication_date >= cutoff_date)) |
                (Paper.publication_date.is_(None) & (Paper.scraped_date >= cutoff_date))
            )
        except ValueError:
            # Invalid days value, ignore the filter
            pass
    
    # Apply sorting
    if sort == "date_asc":
        # Sort by publication_date if available, otherwise by scraped_date
        query = query.order_by(
            func.coalesce(Paper.publication_date, Paper.scraped_date).asc()
        )
    elif sort == "title_asc":
        query = query.order_by(Paper.title.asc())
    elif sort == "title_desc":
        query = query.order_by(Paper.title.desc())
    else:  # default: date_desc
        # Sort by publication_date if available, otherwise by scraped_date
        query = query.order_by(
            desc(func.coalesce(Paper.publication_date, Paper.scraped_date))
        )
    
    papers = query.all()
    journals = db.query(Journal).all()
    topics = db.query(Topic).all()
    
    return templates.TemplateResponse("papers.html", {
        "request": request,
        "papers": papers,
        "journals": journals,
        "topics": topics,
        "selected_journal": journal,
        "selected_author": author,
        "selected_topic": topic,
        "selected_days": days_int,
        "selected_sort": sort
    })

@app.get("/paper/{paper_id}", response_class=HTMLResponse)
async def paper_detail(request: Request, paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return templates.TemplateResponse("paper_detail.html", {
        "request": request,
        "paper": paper
    })

@app.get("/journals", response_class=HTMLResponse)
async def journals(request: Request, db: Session = Depends(get_db)):
    journals = db.query(Journal).all()
    return templates.TemplateResponse("journals.html", {
        "request": request,
        "journals": journals
    })

@app.get("/topics", response_class=HTMLResponse)
async def topics(request: Request, db: Session = Depends(get_db)):
    # Get topics with paper counts
    topic_stats = db.query(
        Topic.name,
        Topic.description,
        func.count(Paper.id).label('paper_count')
    ).join(Paper.topics).group_by(Topic.id).order_by(desc(func.count(Paper.id))).all()
    
    return templates.TemplateResponse("topics.html", {
        "request": request,
        "topic_stats": topic_stats
    })

@app.get("/preprints", response_class=HTMLResponse)
async def preprints(request: Request):
    # Define preprint platforms with their information
    preprint_platforms = [
        {
            "category": "arXiv",
            "platforms": [
                {
                    "name": "arXiv Statistics",
                    "url": "https://arxiv.org/list/stat/new",
                    "description": "New submissions in Statistics",
                    "icon": "fas fa-chart-bar"
                },
                {
                    "name": "arXiv Machine Learning", 
                    "url": "https://arxiv.org/list/cs.LG/recent",
                    "description": "Recent papers in Machine Learning",
                    "icon": "fas fa-robot"
                },
                {
                    "name": "arXiv Statistical Theory",
                    "url": "https://arxiv.org/list/math.ST/recent", 
                    "description": "Recent papers in Statistical Theory",
                    "icon": "fas fa-calculator"
                },
                {
                    "name": "arXiv Methodology",
                    "url": "https://arxiv.org/list/stat.ME/recent",
                    "description": "Recent papers in Statistical Methodology",
                    "icon": "fas fa-tools"
                },
                {
                    "name": "arXiv Applications",
                    "url": "https://arxiv.org/list/stat.AP/recent",
                    "description": "Recent papers in Statistical Applications",
                    "icon": "fas fa-chart-line"
                }
            ]
        },
        {
            "category": "Biology & Medicine",
            "platforms": [
                {
                    "name": "bioRxiv",
                    "url": "https://www.biorxiv.org/",
                    "description": "Preprint server for biology",
                    "icon": "fas fa-dna"
                },
                {
                    "name": "medRxiv", 
                    "url": "https://www.medrxiv.org/",
                    "description": "Preprint server for health sciences",
                    "icon": "fas fa-heartbeat"
                },
                {
                    "name": "PubMed",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/",
                    "description": "Database of biomedical literature",
                    "icon": "fas fa-book-medical"
                }
            ]
        },
        {
            "category": "Economics & Social Sciences",
            "platforms": [
                {
                    "name": "SSRN",
                    "url": "https://www.ssrn.com/",
                    "description": "Social Science Research Network",
                    "icon": "fas fa-users"
                },
                {
                    "name": "IDEAS/RePEc",
                    "url": "https://ideas.repec.org/",
                    "description": "Research Papers in Economics database",
                    "icon": "fas fa-chart-pie"
                }
            ]
        },
        {
            "category": "General Science",
            "platforms": [
                {
                    "name": "Research Square",
                    "url": "https://www.researchsquare.com/",
                    "description": "Preprint platform for all sciences",
                    "icon": "fas fa-square"
                },
                {
                    "name": "OSF Preprints",
                    "url": "https://osf.io/preprints/",
                    "description": "Open Science Framework preprints",
                    "icon": "fas fa-globe"
                },
                {
                    "name": "Preprints.org",
                    "url": "https://www.preprints.org/",
                    "description": "Multidisciplinary preprint platform",
                    "icon": "fas fa-file-alt"
                }
            ]
        }
    ]
    
    return templates.TemplateResponse("preprints.html", {
        "request": request,
        "preprint_platforms": preprint_platforms
    })

@app.post("/scrape")
async def trigger_scrape(db: Session = Depends(get_db)):
    """Manually trigger scraping of all journals"""
    try:
        data_service = DataService(db)
        scrapers = get_all_scrapers()
        
        results = {}
        total_new_papers = 0
        
        for scraper in scrapers:
            try:
                print(f"Starting scraper for {scraper.journal_name}...")
                
                # Scrape for new papers
                papers_data = scraper.scrape_papers()
                count = 0
                for paper_data in papers_data:
                    if data_service.save_paper(paper_data):
                        count += 1
                
                total_new_papers += count
                results[scraper.journal_name] = f"Added {count} new papers (found {len(papers_data)} total)"
                print(f"Completed scraper for {scraper.journal_name}: {count} new papers")
                
            except Exception as e:
                print(f"Error in scraper {scraper.journal_name}: {str(e)}")
                results[scraper.journal_name] = f"Error: {str(e)}"
        
        results["Summary"] = f"Total: {total_new_papers} new papers added across all journals"
        return {"message": "Scraping completed", "results": results}
        
    except Exception as e:
        print(f"General error in scraping: {str(e)}")
        return {"message": "Scraping failed", "error": str(e)}

@app.get("/api/papers")
async def api_papers(
    journal: Optional[str] = None,
    days: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """API endpoint to get papers as JSON"""
    query = db.query(Paper)
    
    if journal:
        query = query.join(Journal).filter(Journal.name == journal)
    
    if days and days.strip():
        try:
            days_int = int(days)
            cutoff_date = datetime.utcnow() - timedelta(days=days_int)
            # Use publication_date if available, otherwise fall back to scraped_date
            query = query.filter(
                (Paper.publication_date.is_not(None) & (Paper.publication_date >= cutoff_date)) |
                (Paper.publication_date.is_(None) & (Paper.scraped_date >= cutoff_date))
            )
        except ValueError:
            pass  # Ignore invalid days value
    
    papers = query.order_by(desc(func.coalesce(Paper.publication_date, Paper.scraped_date))).limit(100).all()
    
    def format_authors(authors):
        """Ensure consistent author ordering with 'others' at the end"""
        author_names = [author.name for author in authors]
        if 'others' in author_names:
            # Move 'others' to the end
            author_names = [name for name in author_names if name != 'others'] + ['others']
        return author_names
    
    return [{
        "id": paper.id,
        "title": paper.title,
        "authors": format_authors(paper.authors),
        "journal": paper.journal.name if paper.journal else None,
        "url": paper.url,
        "publication_date": paper.publication_date.isoformat() if paper.publication_date else None,
        "section": paper.section,
        "scraped_date": paper.scraped_date.isoformat() if paper.scraped_date else None
    } for paper in papers]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)