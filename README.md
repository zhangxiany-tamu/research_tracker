# Research Tracker

A web application that helps researchers keep track of recently accepted research papers from statistics and machine learning journals.

## Journals Tracked

- **AOS**: Annals of Statistics
- **JASA**: Journal of the American Statistical Association  
- **JRSS-B**: Journal of the Royal Statistical Society Series B
- **Biometrika**: Biometrika
- **JMLR**: Journal of Machine Learning Research

## Features

- Automatic scraping of recent papers from journal websites
- Organized browsing by journal, topic, and author
- Automatic topic detection based on paper titles
- Trending topics analysis
- Clean, responsive web interface
- RESTful API for programmatic access

## Installation

1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the web server:
   ```bash
   python run.py
   ```

2. Open your browser and go to: http://localhost:8000

3. Click the "Update" button to scrape recent papers from journals

## API Usage

The application provides a REST API:

- `GET /api/papers` - Get papers as JSON
- `POST /scrape` - Manually trigger scraping
- `GET /api/papers?journal=JMLR&days=30` - Get JMLR papers from last 30 days

## Notes on Data Access

- **AOS** and **JMLR**: Direct web scraping from public pages
- **JASA**, **JRSS-B**, **Biometrika**: These journals block direct scraping (403 errors)
  - Alternative access methods needed (RSS feeds, institutional access, APIs)
  - Current implementation includes placeholder scrapers for these journals

## Topic Detection

Papers are automatically categorized into topics based on keyword matching:

- Machine Learning
- Bayesian Statistics  
- Survival Analysis
- Causal Inference
- High-Dimensional Statistics
- Time Series
- Nonparametric Statistics
- Computational Statistics
- Biostatistics
- Econometrics
- Statistical Learning
- Hypothesis Testing
- Experimental Design

## Database

The application uses SQLite for data storage with the following main tables:
- `papers` - Paper information
- `authors` - Author details
- `journals` - Journal metadata
- `topics` - Research topics
- Association tables for many-to-many relationships

## Development

The application is built with:
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **BeautifulSoup** - Web scraping
- **Bootstrap** - Frontend styling
- **Jinja2** - Template engine