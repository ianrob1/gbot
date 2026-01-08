#!/usr/bin/env python3
"""
Scheduler script that runs twitter_bot.py at random intervals (2-3 times per day).
Runs continuously, sleeping for random periods between 6-12 hours.
"""
import subprocess
import time
import random
import logging
import pathlib
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

BASE_DIR = pathlib.Path(__file__).resolve().parent
BOT_SCRIPT = BASE_DIR / "twitter_bot.py"

# Configuration: Random interval between 6-12 hours (ensures 2-3 runs per day)
MIN_INTERVAL_HOURS = 6
MAX_INTERVAL_HOURS = 12
JITTER_MINUTES = 30  # Add small random jitter to avoid predictable patterns


def calculate_next_interval():
    """Calculate random interval in seconds between MIN and MAX hours."""
    # Base interval: 6-12 hours
    base_hours = random.uniform(MIN_INTERVAL_HOURS, MAX_INTERVAL_HOURS)
    base_seconds = int(base_hours * 3600)
    
    # Add random jitter: ±30 minutes
    jitter_seconds = random.randint(-JITTER_MINUTES * 60, JITTER_MINUTES * 60)
    
    total_seconds = base_seconds + jitter_seconds
    return max(3600, total_seconds)  # Ensure at least 1 hour


def run_bot():
    """Execute the twitter bot script as a subprocess."""
    if not BOT_SCRIPT.exists():
        logger.error(f"Bot script not found: {BOT_SCRIPT}")
        return False
    
    logger.info("=" * 60)
    logger.info("Starting bot execution...")
    logger.info("=" * 60)
    
    try:
        # Run the bot script
        result = subprocess.run(
            ["python3", str(BOT_SCRIPT)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Log output
        if result.stdout:
            logger.info("Bot stdout:")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
        
        if result.stderr:
            logger.warning("Bot stderr:")
            for line in result.stderr.strip().split('\n'):
                logger.warning(f"  {line}")
        
        if result.returncode == 0:
            logger.info("Bot execution completed successfully")
            return True
        else:
            logger.error(f"Bot execution failed with exit code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Bot execution timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        return False


def main():
    """Main scheduler loop."""
    logger.info("=" * 60)
    logger.info("Twitter Bot Scheduler Started")
    logger.info(f"Bot script: {BOT_SCRIPT}")
    logger.info(f"Interval range: {MIN_INTERVAL_HOURS}-{MAX_INTERVAL_HOURS} hours")
    logger.info("=" * 60)
    
    # Run immediately on startup (optional - comment out if you want to wait first)
    logger.info("Running initial bot execution...")
    run_bot()
    
    # Main scheduling loop
    while True:
        try:
            # Calculate next interval
            interval_seconds = calculate_next_interval()
            interval_hours = interval_seconds / 3600
            next_run = datetime.now() + timedelta(seconds=interval_seconds)
            
            logger.info("=" * 60)
            logger.info(f"Sleeping for {interval_hours:.2f} hours ({interval_seconds} seconds)")
            logger.info(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)
            
            # Sleep for the calculated interval
            time.sleep(interval_seconds)
            
            # Run the bot
            run_bot()
            
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user. Shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in scheduler loop: {e}", exc_info=True)
            # Wait a bit before retrying to avoid tight error loops
            logger.info("Waiting 5 minutes before retrying...")
            time.sleep(300)


if __name__ == "__main__":
    main()
