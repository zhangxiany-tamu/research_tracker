# Research Tracker

A web application for tracking recent papers from leading statistics and machine learning journals.

## Features

- **Automated scraping** from 5 major journals: AOS, JASA, JRSSB, Biometrika, JMLR
- **Smart filtering** by journal, author, topic, and date
- **Topic detection** using keyword matching
- **Real-time updates** with manual refresh capability
- **Preprint links** to arXiv, bioRxiv, medRxiv, SSRN, and other platforms
- **Responsive design** with modern UI

## Quick Start

```bash
pip install -r requirements.txt
python run.py
```

Visit http://localhost:8000

## Journals Tracked

- **Annals of Statistics** (64 papers)
- **Journal of Machine Learning Research** (115 papers with abstracts)
- **Journal of the American Statistical Association** (66 papers)
- **Journal of the Royal Statistical Society Series B** (40 papers)
- **Biometrika** (27 papers)

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, BeautifulSoup
- **Frontend**: Bootstrap 5, Font Awesome
- **Database**: SQLite
- **Deployment**: Python 3.8+

## License

MIT