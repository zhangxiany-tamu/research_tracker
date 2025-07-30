# Research Tracker - GitHub Actions Deployment Guide

## Quick Setup Summary

✅ **Status**: Ready for GitHub Actions deployment
✅ **Scrapers**: All 5 journals working locally  
✅ **Cloud API**: Accessible and functional
✅ **Data Format**: Compatible with cloud sync

## Files Ready for Deployment

### Core Application Files
- ✅ `app/` - Complete scraper and database logic
- ✅ `templates/` - Web interface
- ✅ `static/` - CSS and assets
- ✅ `requirements.txt` - Python dependencies
- ✅ `run.py` - Local development server

### GitHub Actions Files (NEW)
- ✅ `.github/workflows/daily-scrape.yml` - Daily automated scraping
- ✅ `.github/workflows/manual-scrape.yml` - Manual testing workflow
- ✅ `scripts/scrape_and_sync.py` - Core scraping logic
- ✅ `GITHUB_ACTIONS_SETUP.md` - Detailed setup instructions

## Deployment Steps

### 1. Create GitHub Repository
```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit with GitHub Actions setup"

# Create repository on GitHub and push
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/research-tracker.git
git push -u origin main
```

### 2. Enable GitHub Actions
1. Go to your repository on GitHub
2. Click the **Actions** tab
3. If prompted, click **"I understand my workflows, go ahead and enable them"**
4. You should see two workflows available:
   - **Daily Paper Scraping** (runs daily at 6 AM UTC)
   - **Manual Paper Scraping** (manual trigger for testing)

### 3. Test Manual Workflow
1. In the Actions tab, click **Manual Paper Scraping**
2. Click **Run workflow**
3. Leave the cloud URL as default: `https://research-tracker-466018.uc.r.appspot.com`
4. Click **Run workflow** button
5. Monitor the run - should complete successfully in ~10 minutes

### 4. Monitor Daily Workflow
- The daily workflow will run automatically at 6 AM UTC every day
- Check the Actions tab to see run history and status
- Each run creates a detailed summary of papers scraped and synced

## Expected Behavior

### Daily Workflow Results
- **JASA**: 143 papers with publication dates
- **JRSSB**: 45 papers with publication dates  
- **Biometrika**: 29 papers with publication dates
- **AOS**: 64 papers (ordered by scraped date)
- **JMLR**: 115 papers (ordered by scraped date)
- **Total**: ~396 papers

### Smart Sync Process
- ✅ Only adds **new papers** that don't exist in cloud database
- ✅ Skips **existing papers** to prevent duplicates
- ✅ Preserves **publication dates** for JASA, JRSSB, Biometrika
- ✅ Maintains **correct ordering** for all journals
- ✅ Handles **individual journal failures** gracefully

## Benefits of This Approach

### ✅ Solves Cloud Scraping Issues
- **Problem**: Academic journals block cloud IPs
- **Solution**: Use GitHub's infrastructure for scraping
- **Result**: Reliable daily updates regardless of IP restrictions

### ✅ Automated and Reliable
- **Frequency**: Daily at 6 AM UTC (customizable)
- **Monitoring**: Detailed logs and summaries for each run
- **Error Handling**: Individual journal failures don't stop the process
- **Cost**: Free with GitHub Actions

### ✅ Maintains Data Quality  
- **Ordering**: Matches journal websites exactly
- **Dates**: Proper publication dates where available
- **Completeness**: All 396 papers maintained consistently
- **Integrity**: No duplicates, proper author attribution

## Troubleshooting

### If Daily Workflow Fails
1. **Check the Actions tab** for error details
2. **Common issues**:
   - Journal website changed structure → Update scrapers
   - Rate limiting → Add delays to scrapers
   - Cloud database unreachable → Check cloud status

### If Papers Are Missing
1. **Check individual journal results** in workflow summary
2. **Compare counts** with expected numbers (396 total)
3. **Run manual workflow** to test specific issues

### If Cloud Sync Fails
1. **Verify cloud URL** is accessible: https://research-tracker-466018.uc.r.appspot.com
2. **Check API endpoint**: `/api/sync-papers` should accept POST requests
3. **Review error logs** in workflow details

## Migration from Manual Updates

### Before GitHub Actions
- ❌ Manual scraping required every time
- ❌ Cloud scraping blocked by journals
- ❌ Inconsistent updates
- ❌ Required local environment setup

### After GitHub Actions  
- ✅ **Fully automated** daily updates
- ✅ **Bypasses IP restrictions** using GitHub infrastructure
- ✅ **Consistent data quality** with proper error handling
- ✅ **Zero maintenance** once set up
- ✅ **Detailed monitoring** and alerting

## Next Steps

1. **Deploy to GitHub** following the steps above
2. **Test manual workflow** to verify everything works
3. **Monitor first few daily runs** to ensure stability
4. **Optionally customize** schedule or add more journals
5. **Enjoy automated** daily paper updates! 🎉

The system is now ready for production deployment with automated daily scraping via GitHub Actions!