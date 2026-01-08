# Twitter Bot Deployment Guide

This guide will help you deploy your Twitter bot to run automatically 2-3 times per day on a cloud platform.

## Prerequisites

- A GitHub account (for version control)
- A Railway or Render account (free tiers available)
- Twitter API credentials (already configured in your bot)

## Option 1: Deploy to Railway

Railway is a modern platform that makes deployment simple.

### Step 1: Prepare Your Repository

1. Initialize git (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. Create a GitHub repository and push your code:
   ```bash
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

### Step 2: Deploy to Railway

1. Go to [railway.app](https://railway.app) and sign up/login
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect the `Procfile` and start deploying

### Step 3: Configure Environment Variables

1. In your Railway project, go to the "Variables" tab
2. Add the following environment variables:
   - `TWITTER_API_KEY` - Your Twitter API key
   - `TWITTER_API_SECRET` - Your Twitter API secret
   - `TWITTER_ACCESS_TOKEN` - Your Twitter access token
   - `TWITTER_ACCESS_TOKEN_SECRET` - Your Twitter access token secret

3. Railway will automatically redeploy with the new variables

### Step 4: Upload Required Files

Railway needs access to your CSV file and other data files. You have two options:

**Option A: Include in Git (if file is small)**
- Add `gmanifesto_tweets.csv` to your repository
- Commit and push: `git add gmanifesto_tweets.csv && git commit -m "Add tweets CSV" && git push`

**Option B: Upload via Railway Dashboard**
- Go to your Railway project
- Use the "Files" tab or connect via SSH to upload `gmanifesto_tweets.csv`
- Place it in the project root directory

### Step 5: Verify Deployment

1. Check the "Deployments" tab to see if deployment succeeded
2. View logs in the "Logs" tab - you should see scheduler messages
3. The bot will run immediately on startup, then wait for the next scheduled interval

## Option 2: Deploy to Render

Render is another excellent option with a free tier.

### Step 1: Prepare Your Repository

Same as Railway - ensure your code is in a GitHub repository.

### Step 2: Deploy to Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Background Worker"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `twitter-bot` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 scheduler.py`
   - **Plan**: Free (or paid if you prefer)

### Step 3: Configure Environment Variables

1. In the Render dashboard, scroll to "Environment Variables"
2. Add the same four Twitter API variables as listed in Railway section
3. Click "Save Changes" - Render will redeploy automatically

### Step 4: Upload Required Files

Similar to Railway, you can either:
- Include `gmanifesto_tweets.csv` in your Git repository
- Use Render's file system (via SSH or dashboard) to upload it

### Step 5: Verify Deployment

1. Check the "Logs" tab for scheduler activity
2. The bot should start running automatically

## Monitoring Your Bot

### Viewing Logs

- **Railway**: Go to your project → "Logs" tab
- **Render**: Go to your service → "Logs" tab

You'll see messages like:
```
2024-01-01 12:00:00 - INFO - Twitter Bot Scheduler Started
2024-01-01 12:00:05 - INFO - Starting bot execution...
2024-01-01 12:00:10 - INFO - Tweet posted. ID: 1234567890
2024-01-01 12:00:10 - INFO - Sleeping for 8.5 hours
2024-01-01 12:00:10 - INFO - Next run scheduled for: 2024-01-01 20:30:10
```

### Checking Bot Activity

- Monitor your Twitter account to see when tweets are posted
- Check the logs to verify the scheduler is running
- The bot will run 2-3 times per day at random intervals (6-12 hours apart)

## Troubleshooting

### Bot Not Running

1. **Check logs** for error messages
2. **Verify environment variables** are set correctly
3. **Ensure CSV file exists** - check logs for "CSV not found" errors
4. **Check Twitter API rate limits** - if you see 429 errors, the bot will retry later

### Bot Running Too Frequently/Infrequently

Edit `scheduler.py` and adjust:
- `MIN_INTERVAL_HOURS` - minimum hours between runs (default: 6)
- `MAX_INTERVAL_HOURS` - maximum hours between runs (default: 12)

Then redeploy your changes.

### CSV File Not Found

Make sure `gmanifesto_tweets.csv` is:
- Included in your Git repository, OR
- Uploaded to the cloud platform's file system

### Lock File Issues

If you see "Another run is already active" errors, the lock file may be stuck. The scheduler handles this automatically, but if issues persist, you may need to manually remove `posted.lock` via SSH or platform file access.

## Local Testing

Before deploying, test locally:

1. Set environment variables:
   ```bash
   export TWITTER_API_KEY="your_key"
   export TWITTER_API_SECRET="your_secret"
   export TWITTER_ACCESS_TOKEN="your_token"
   export TWITTER_ACCESS_TOKEN_SECRET="your_token_secret"
   ```

2. Run the scheduler:
   ```bash
   python3 scheduler.py
   ```

3. Let it run for a few minutes to verify it works correctly

## Cost Considerations

- **Railway**: Free tier includes $5/month credit (usually enough for a simple bot)
- **Render**: Free tier available, but services may sleep after inactivity (not ideal for schedulers)
- Both platforms offer paid plans if you need more resources

## Security Notes

- Never commit `.env` files or hardcoded API keys to Git
- Use environment variables for all sensitive credentials
- The `.gitignore` file is configured to exclude sensitive files

## Updating the Bot

To update your bot:

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update bot"
   git push
   ```
3. Railway/Render will automatically detect changes and redeploy

## Stopping the Bot

- **Railway**: Go to project → "Settings" → "Delete Project" or pause the service
- **Render**: Go to service → "Settings" → "Delete Service" or pause it
