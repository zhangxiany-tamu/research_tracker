from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between papers and authors
paper_authors = Table(
    'paper_authors',
    Base.metadata,
    Column('paper_id', Integer, ForeignKey('papers.id'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id'), primary_key=True),
    Column('author_order', Integer, nullable=False, default=0)
)

# Association table for many-to-many relationship between papers and topics
paper_topics = Table(
    'paper_topics',
    Base.metadata,
    Column('paper_id', Integer, ForeignKey('papers.id'), primary_key=True),
    Column('topic_id', Integer, ForeignKey('topics.id'), primary_key=True)
)

class Journal(Base):
    __tablename__ = 'journals'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    abbreviation = Column(String(20), unique=True)
    url = Column(String(500))
    papers_url = Column(String(500))
    
    papers = relationship("Paper", back_populates="journal")

class Author(Base):
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    email = Column(String(200), nullable=True)
    affiliation = Column(String(500), nullable=True)
    
    papers = relationship("Paper", secondary=paper_authors, back_populates="authors")

class Topic(Base):
    __tablename__ = 'topics'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text, nullable=True)
    
    papers = relationship("Paper", secondary=paper_topics, back_populates="topics")

class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True)
    abstract = Column(Text, nullable=True)
    doi = Column(String(200), nullable=True, unique=True)
    url = Column(String(500), nullable=True)
    pdf_url = Column(String(500), nullable=True)
    bibtex = Column(Text, nullable=True)  # Store BibTeX citation
    publication_date = Column(DateTime, nullable=True)
    accepted_date = Column(DateTime, nullable=True)
    scraped_date = Column(DateTime, default=datetime.utcnow)
    section = Column(String(100), nullable=True)  # Added section field
    journal_id = Column(Integer, ForeignKey('journals.id'))
    
    journal = relationship("Journal", back_populates="papers")
    authors = relationship("Author", secondary=paper_authors, back_populates="papers", order_by=paper_authors.c.author_order)
    topics = relationship("Topic", secondary=paper_topics, back_populates="papers")