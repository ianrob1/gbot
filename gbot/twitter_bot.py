#!/usr/bin/env python3
import csv
import random
import pathlib
import tweepy
import sys
import hashlib
import os

# -------- CONFIG --------

BASE_DIR = pathlib.Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "gmanifesto_tweets.csv"   # change if needed
MAX_RANGE = 1000

# Stores hashes of already-posted tweets (local only)
POSTED_FILE = BASE_DIR / "posted_hashes.txt"
LOCK_FILE = BASE_DIR / "posted.lock"

# Use env vars OR paste keys directly (env vars take precedence)
API_KEY = os.getenv("TWITTER_API_KEY", "uq4BmQs7QVzScSXKApREyc320")
API_SECRET = os.getenv("TWITTER_API_SECRET", "G0x1AmamLuqvuRwpioJczzNAo3H1RXv4HS8WqfjgPjfwNBoWMg")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "1013977101198876672-YgMxHSqhjq99RA4t9tjpViBLWne0Rq")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "4VKev0L6nEllXyziRxC4e6d9i2rHAR1smLARqNm9DEIfr")

# -------- HELPERS --------

def load_tweets():
    if not CSV_FILE.exists():
        print(f"CSV not found: {CSV_FILE}")
        return []

    with CSV_FILE.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return []

    tweets = []
    first = rows[0]

    has_header = any(
        isinstance(cell, str) and cell.strip().lower() == "text"
        for cell in first
    )

    start = 1 if has_header else 0
    col = (
        next(
            i for i, cell in enumerate(first)
            if isinstance(cell, str) and cell.strip().lower() == "text"
        )
        if has_header
        else 0
    )

    for row in rows[start:]:
        if len(row) > col and row[col]:
            tweets.append(row[col].strip())

    return tweets


def clean_tweet(raw: str):
    """
    - Remove pic.twitter.com links
    - Skip ANY tweet that contains http/https
    - Convert double spaces to blank lines
    - Trim whitespace
    - Enforce 280 chars
    """
    if not raw:
        return None

    text = raw.replace("\xa0", " ").strip()
    lower = text.lower()

    # Remove pic.twitter.com but keep text before it
    if "pic.twitter.com" in lower:
        text = text[:lower.index("pic.twitter.com")].strip()
        lower = text.lower()

    # Skip any tweet containing links
    if "http://" in lower or "https://" in lower:
        return None

    # Double spaces → paragraph break
    text = text.replace("  ", "\n\n")

    # Clean line indentation
    text = "\n".join(line.strip() for line in text.splitlines()).strip()

    if not text:
        return None

    if len(text) > 280:
        text = text[:277] + "..."

    return text


def _normalize_for_hash(text: str) -> str:
    # Stable normalization so identical tweets hash identically
    return "\n".join(line.rstrip() for line in text.strip().splitlines()).strip()


def tweet_hash(text: str) -> str:
    norm = _normalize_for_hash(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def load_posted_hashes():
    if not POSTED_FILE.exists():
        return set()
    return set(POSTED_FILE.read_text(encoding="utf-8").splitlines())


def mark_posted(text: str):
    h = tweet_hash(text)
    with POSTED_FILE.open("a", encoding="utf-8") as f:
        f.write(h + "\n")


def pick_tweet(tweets, posted_hashes):
    subset = tweets[:min(MAX_RANGE, len(tweets))]
    random.shuffle(subset)

    for raw in subset:
        cleaned = clean_tweet(raw)
        if not cleaned:
            continue

        if tweet_hash(cleaned) in posted_hashes:
            continue

        return cleaned

    return None


def create_client():
    return tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )


def get_follower_count(client: tweepy.Client):
    """
    Fetches the authenticated user's follower count using v2.
    Returns an int, or None if unavailable.
    """
    try:
        me = client.get_me(user_fields=["public_metrics"])
        if not me or not me.data:
            return None
        metrics = getattr(me.data, "public_metrics", None) or {}
        return metrics.get("followers_count")
    except tweepy.TweepyException:
        return None


def acquire_lock():
    """
    Prevent concurrent runs from posting duplicates.
    Creates LOCK_FILE exclusively; if it already exists, another run is active.
    Returns a file descriptor that must be closed; also removes lock on release.
    """
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        return fd
    except FileExistsError:
        return None


def release_lock(fd):
    try:
        if fd is not None:
            os.close(fd)
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        # Do not crash on cleanup errors
        pass


# -------- MAIN --------

def main():
    lock_fd = acquire_lock()
    if lock_fd is None:
        print(f"Another run is already active (lock exists): {LOCK_FILE}")
        sys.exit(1)

    client = create_client()

    try:
        tweets = load_tweets()
        if not tweets:
            print("No tweets loaded.")
            sys.exit(1)

        posted_hashes = load_posted_hashes()

        tweet = pick_tweet(tweets, posted_hashes)
        if not tweet:
            print("No valid NEW tweet found after filtering (all candidates already posted).")
            sys.exit(1)

        print("Posting:")
        print("-" * 40)
        print(tweet)
        print("-" * 40)

        try:
            resp = client.create_tweet(text=tweet)
            print("Tweet posted. ID:", resp.data.get("id"))
            # Only mark as posted if the tweet was successfully created
            mark_posted(tweet)
        except tweepy.TooManyRequests:
            print("ERROR: Rate limited (429). Try again later.")
        except tweepy.TweepyException as e:
            print("ERROR posting tweet:", e)

        # Terminal-only follower count display
        followers = get_follower_count(client)
        if followers is None:
            print("Follower count: (unavailable)")
        else:
            print(f"Follower count: {followers}")

    finally:
        release_lock(lock_fd)


if __name__ == "__main__":
    main()
