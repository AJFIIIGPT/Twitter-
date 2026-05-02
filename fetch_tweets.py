from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

ACCOUNTS_FILE = Path("accounts.txt")
RAW_TWEETS_FILE = Path("raw_tweets.txt")
OUTPUT_FILE = Path("tweets_last24h.csv")

TICKER_PATTERN = re.compile(r"\$([A-Z]{1,5})\b")
POLITICS_TERMS = {
    "election", "senate", "congress", "democrat", "republican", "president", "policy", "geopolitics", "politics"
}
UI_NOISE_TERMS = {"show more", "view replies", "promoted", "who to follow", "trending"}


@dataclass
class Tweet:
    timestamp: datetime
    author: str
    text: str


def load_accounts(path: Path = ACCOUNTS_FILE) -> set[str]:
    if not path.exists():
        return set()
    return {line.strip().lstrip("@").lower() for line in path.read_text().splitlines() if line.strip() and not line.strip().startswith("#")}


def parse_manual_raw(path: Path = RAW_TWEETS_FILE) -> list[Tweet]:
    """Expected line format:
    2026-05-02T13:15:00Z|username|tweet text here
    """
    tweets: list[Tweet] = []
    if not path.exists():
        return tweets

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        ts_raw, author, text = parts
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        tweets.append(Tweet(timestamp=ts.astimezone(timezone.utc), author=author.strip().lstrip("@"), text=text.strip()))
    return tweets


def fetch_from_api_placeholder(accounts: Iterable[str]) -> list[Tweet]:
    """Placeholder for future X API integration.

    Add credentials and API client usage here later.
    """
    _ = list(accounts)
    return []


def is_noise_or_filtered(tweet: Tweet) -> bool:
    text_lower = tweet.text.lower()
    if any(k in text_lower for k in UI_NOISE_TERMS):
        return True
    if any(k in text_lower for k in POLITICS_TERMS):
        return True
    # repost/retweet without commentary
    stripped = tweet.text.strip()
    if stripped.startswith(("RT @", "Repost @")) and "//" not in stripped:
        return True
    # ad-like/promoted language
    if "sponsored" in text_lower or "ad:" in text_lower:
        return True
    return False


def keep_last_24h(tweets: list[Tweet]) -> list[Tweet]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return [t for t in tweets if t.timestamp >= cutoff]


def deduplicate(tweets: list[Tweet]) -> list[Tweet]:
    seen = set()
    unique: list[Tweet] = []
    for t in tweets:
        key = (t.author.lower(), t.text.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(t)
    return unique


def is_real_pitch(text: str) -> bool:
    t = text.lower()
    has_ticker = bool(TICKER_PATTERN.search(text))
    thesis_terms = ["because", "thesis", "why", "expect", "catalyst", "earnings", "guidance", "valuation", "setup"]
    return has_ticker and any(k in t for k in thesis_terms)


def to_dataframe(tweets: list[Tweet]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"timestamp": t.timestamp.isoformat(), "author": t.author, "text": t.text, "is_real_pitch": is_real_pitch(t.text)} for t in tweets]
    )


def run(mode: str = "manual") -> pd.DataFrame:
    accounts = load_accounts()
    tweets = parse_manual_raw() if mode == "manual" else fetch_from_api_placeholder(accounts)

    if accounts:
        tweets = [t for t in tweets if t.author.lower() in accounts]

    tweets = keep_last_24h(tweets)
    tweets = [t for t in tweets if not is_noise_or_filtered(t)]
    tweets = deduplicate(tweets)

    df = to_dataframe(tweets)
    df.to_csv(OUTPUT_FILE, index=False)
    return df


if __name__ == "__main__":
    df = run(mode="manual")
    ticker_mentions = int(df["text"].str.count(TICKER_PATTERN).sum()) if not df.empty else 0
    real_pitches = int(df["is_real_pitch"].sum()) if not df.empty else 0
    print(f"Saved {len(df)} posts to {OUTPUT_FILE}")
    print(f"total posts collected: {len(df)}")
    print(f"total ticker mentions: {ticker_mentions}")
    print(f"total real pitches: {real_pitches}")
