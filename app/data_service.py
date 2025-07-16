from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Paper, Author, Journal, Topic, paper_authors
from typing import Dict, List, Optional
import re

class DataService:
    def __init__(self, db: Session):
        self.db = db
        self._ensure_journals_exist()
    
    def _ensure_journals_exist(self):
        """Ensure all journals exist in the database"""
        journals_data = [
            {"name": "Annals of Statistics", "abbreviation": "AOS", 
             "url": "https://imstat.org/journals-and-publications/annals-of-statistics/",
             "papers_url": "https://imstat.org/journals-and-publications/annals-of-statistics/annals-of-statistics-future-papers/"},
            {"name": "Journal of the American Statistical Association", "abbreviation": "JASA",
             "url": "https://www.tandfonline.com/journals/uasa20",
             "papers_url": "https://www.tandfonline.com/action/showAxaArticles?journalCode=uasa20"},
            {"name": "Journal of the Royal Statistical Society Series B", "abbreviation": "JRSSB",
             "url": "https://academic.oup.com/jrsssb",
             "papers_url": "https://academic.oup.com/jrsssb/advance-articles"},
            {"name": "Biometrika", "abbreviation": "Biometrika",
             "url": "https://academic.oup.com/biomet",
             "papers_url": "https://academic.oup.com/biomet/advance-articles"},
            {"name": "Journal of Machine Learning Research", "abbreviation": "JMLR",
             "url": "https://www.jmlr.org/",
             "papers_url": "https://www.jmlr.org/"}
        ]
        
        for journal_data in journals_data:
            existing = self.db.query(Journal).filter(Journal.name == journal_data["name"]).first()
            if not existing:
                journal = Journal(**journal_data)
                self.db.add(journal)
        
        self.db.commit()
    
    def get_or_create_author(self, name: str) -> Author:
        """Get existing author or create new one"""
        author = self.db.query(Author).filter(Author.name == name).first()
        if not author:
            author = Author(name=name)
            self.db.add(author)
            self.db.flush()  # Get the ID without committing
        return author
    
    def get_or_create_topic(self, name: str) -> Topic:
        """Get existing topic or create new one"""
        topic = self.db.query(Topic).filter(Topic.name == name).first()
        if not topic:
            topic = Topic(name=name)
            self.db.add(topic)
            self.db.flush()  # Get the ID without committing
        return topic
    
    def extract_topics_from_title(self, title: str) -> List[str]:
        """Extract potential topics from paper title using keyword matching"""
        title_lower = title.lower()
        
        # Define topic keywords
        topic_keywords = {
            "Machine Learning": ["machine learning", "neural network", "deep learning", "artificial intelligence", "ai", "classification", "regression", "supervised learning", "unsupervised learning"],
            "Bayesian Statistics": ["bayesian", "bayes", "mcmc", "posterior", "prior", "markov chain"],
            "Survival Analysis": ["survival", "hazard", "kaplan-meier", "cox", "time-to-event"],
            "Causal Inference": ["causal", "causality", "treatment effect", "propensity", "instrumental variable"],
            "High-Dimensional Statistics": ["high-dimensional", "sparse", "lasso", "ridge", "penalized", "regularization"],
            "Time Series": ["time series", "temporal", "forecasting", "autoregressive", "arima"],
            "Nonparametric Statistics": ["nonparametric", "kernel", "bandwidth", "smoothing"],
            "Computational Statistics": ["computational", "algorithm", "optimization", "simulation", "monte carlo"],
            "Biostatistics": ["biostatistics", "clinical trial", "medical", "epidemiology", "genetics"],
            "Econometrics": ["econometric", "economic", "panel data", "endogeneity"],
            "Statistical Learning": ["statistical learning", "cross-validation", "model selection", "prediction"],
            "Hypothesis Testing": ["testing", "p-value", "significance", "multiple testing"],
            "Experimental Design": ["experimental design", "randomization", "factorial", "design of experiments"]
        }
        
        detected_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics
    
    def save_paper(self, paper_data: Dict) -> bool:
        """Save paper data to database, return True if new paper was added"""
        try:
            # Check if paper already exists (by title and journal)
            journal = self.db.query(Journal).filter(Journal.name == paper_data['journal']).first()
            if not journal:
                return False
            
            existing = self.db.query(Paper).filter(
                Paper.title == paper_data['title'],
                Paper.journal_id == journal.id
            ).first()
            
            if existing:
                return False  # Paper already exists
            
            # Create new paper
            paper = Paper(
                title=paper_data['title'],
                abstract=paper_data.get('abstract'),
                doi=paper_data.get('doi'),
                url=paper_data.get('url'),
                pdf_url=paper_data.get('pdf_url'),
                bibtex=paper_data.get('bibtex'),
                publication_date=paper_data.get('publication_date'),
                accepted_date=paper_data.get('accepted_date'),
                scraped_date=paper_data.get('scraped_date'),
                section=paper_data.get('section'),
                journal_id=journal.id
            )
            
            self.db.add(paper)
            self.db.flush()  # Get paper ID
            
            # Add authors with proper ordering
            if 'authors' in paper_data and paper_data['authors']:
                for order, author_name in enumerate(paper_data['authors']):
                    if author_name.strip():
                        author = self.get_or_create_author(author_name.strip())
                        # Insert into association table with order
                        self.db.execute(
                            paper_authors.insert().values(
                                paper_id=paper.id,
                                author_id=author.id,
                                author_order=order
                            )
                        )
            
            # Auto-detect and add topics
            detected_topics = self.extract_topics_from_title(paper_data['title'])
            for topic_name in detected_topics:
                topic = self.get_or_create_topic(topic_name)
                paper.topics.append(topic)
            
            self.db.commit()
            return True
            
        except IntegrityError:
            self.db.rollback()
            return False
        except Exception as e:
            self.db.rollback()
            print(f"Error saving paper: {e}")
            return False
    
    def get_trending_topics(self, days: int = 30) -> List[Dict]:
        """Get trending topics based on recent papers"""
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        trending = self.db.query(
            Topic.name,
            func.count(Paper.id).label('paper_count')
        ).join(Paper.topics).join(Paper).filter(
            Paper.scraped_date >= cutoff_date
        ).group_by(Topic.id).order_by(
            func.count(Paper.id).desc()
        ).limit(10).all()
        
        return [{"topic": topic, "count": count} for topic, count in trending]