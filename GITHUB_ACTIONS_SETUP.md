# GitHub Actions Setup for Daily Paper Scraping

This document explains how to set up GitHub Actions to automatically scrape papers daily and sync them to your cloud database.

## Overview

Since academic journal websites block scraping from cloud environments, we use GitHub Actions to:
1. **Scrape papers** from journal websites using GitHub's infrastructure
2. **Sync the data** to your cloud database via API calls
3. **Run automatically** every day at 6 AM UTC
4. **Provide detailed logs** and summaries of each run

## Files Created

### 1. `.github/workflows/daily-scrape.yml`
- **Purpose**: Main daily scraping workflow
- **Schedule**: Runs daily at 6 AM UTC
- **Features**: 
  - Scrapes all 5 journals (JASA, JRSSB, Biometrika, AOS, JMLR)
  - Syncs data to cloud database
  - Creates detailed summary reports
  - Handles errors gracefully

### 2. `.github/workflows/manual-scrape.yml`
- **Purpose**: Manual testing workflow
- **Trigger**: Manual only (for testing)
- **Features**: 
  - Same functionality as daily scrape
  - Allows custom cloud URL input
  - Useful for debugging and testing

### 3. `scripts/scrape_and_sync.py`
- **Purpose**: Core scraping and syncing logic
- **Usage**: Can be run locally or by GitHub Actions
- **Features**:
  - Creates fresh local database
  - Scrapes all journals systematically
  - Converts data for cloud sync
  - Comprehensive error handling

## Setup Instructions

### Step 1: Repository Setup
1. **Push your code** to a GitHub repository
2. **Ensure all files** are committed including:
   - `.github/workflows/` directory
   - `scripts/scrape_and_sync.py`
   - `requirements.txt`
   - All scraper code in `app/`

### Step 2: Configure Secrets (Optional)
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Add repository secret:
   - **Name**: `CLOUD_URL`
   - **Value**: `https://research-tracker-466018.uc.r.appspot.com`
   - (This is optional - the workflow uses this URL by default)

### Step 3: Enable Actions
1. Go to your repository's **Actions** tab
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. You should see two workflows:
   - **Daily Paper Scraping** (scheduled)
   - **Manual Paper Scraping** (manual)

### Step 4: Test Manual Run
1. Go to **Actions** tab
2. Click **Manual Paper Scraping**
3. Click **Run workflow**
4. Leave cloud URL as default or enter a custom one
5. Click **Run workflow** button
6. Monitor the run to ensure everything works

## How It Works

### Daily Workflow Process
```
1. GitHub Action starts (6 AM UTC daily)
2. Sets up Python environment
3. Installs dependencies
4. Creates fresh local SQLite database
5. Runs all 5 scrapers sequentially:
   - JASA (143 papers with publication dates)
   - JRSSB (45 papers with publication dates)  
   - Biometrika (29 papers with publication dates)
   - AOS (64 papers with scraped dates)
   - JMLR (115 papers with scraped dates)
6. Converts data to JSON format
7. Sends POST request to /api/sync-papers
8. Updates cloud database with new papers only
9. Creates summary report
10. Uploads artifacts for debugging
```

### Data Sync Process
- **Smart Updates**: Only adds papers that don't already exist
- **No Duplicates**: Existing papers are automatically skipped
- **Date Handling**: Preserves publication dates and scraped dates
- **Error Recovery**: Individual journal failures don't stop the whole process

## Monitoring and Maintenance

### Check Run Status
1. Go to **Actions** tab in your repository
2. Look for recent **Daily Paper Scraping** runs
3. Green checkmark = success, Red X = failure
4. Click on any run to see detailed logs

### View Summary Reports
Each run creates a summary table showing:
- Papers found per journal
- Papers saved per journal
- Success/failure status
- Total counts

### Download Debug Data
If something goes wrong:
1. Click on the failed workflow run
2. Scroll to bottom and find **Artifacts**
3. Download **scraped-papers** or **scrape-results**
4. Contains JSON files with raw data for debugging

### Customize Schedule
To change the daily schedule, edit `.github/workflows/daily-scrape.yml`:
```yaml
schedule:
  # Run at different time (example: 2 PM UTC)
  - cron: '0 14 * * *'
```

### Handle Failures
Common failure scenarios and solutions:

1. **Scraper Blocked**: Journal website might be blocking GitHub IPs
   - Solution: Update User-Agent strings in scrapers
   - Or add delays between requests

2. **Cloud Sync Failed**: Network issues or cloud database down
   - Solution: Workflow will retry automatically
   - Check cloud database status manually

3. **Data Format Issues**: Changes in journal website structure
   - Solution: Update scraper selectors in `app/scrapers.py`
   - Test locally first, then push changes

## Benefits

✅ **Automated**: No manual intervention needed
✅ **Reliable**: Runs daily regardless of cloud environment
✅ **Scalable**: Easy to add more journals or change frequency  
✅ **Monitored**: Detailed logs and failure notifications
✅ **Cost-Free**: GitHub Actions provides free compute time
✅ **Bypass Restrictions**: Uses GitHub's IP ranges instead of cloud IPs

## Expected Results

After setup, you should see:
- **Daily updates** to your cloud database
- **396+ papers** maintained across all journals
- **New papers** automatically detected and added
- **Consistent uptime** regardless of scraping restrictions
- **Detailed monitoring** of the entire process

The system will maintain your research tracker with fresh papers daily, completely automatically! 🎉