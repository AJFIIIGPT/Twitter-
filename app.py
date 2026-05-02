import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

TWEETS_FILE = Path("tweets_last24h.csv")
TICKER_PATTERN = re.compile(r"\$([A-Z]{1,5})\b")


@dataclass
class Mention:
    ticker: str
    author: str
    text: str
    timestamp: str


def extract_tickers(text: str) -> List[str]:
    return TICKER_PATTERN.findall(text or "")


def infer_sentiment(text: str) -> str:
    t = (text or "").lower()
    bullish = ["buy", "long", "bull", "breakout", "upside", "beat", "accumulate"]
    bearish = ["short", "bear", "downside", "miss", "sell", "dump", "avoid"]
    bull_hits = sum(k in t for k in bullish)
    bear_hits = sum(k in t for k in bearish)
    if bull_hits > bear_hits:
        return "Bullish"
    if bear_hits > bull_hits:
        return "Bearish"
    return "Neutral"


def make_thesis(texts: List[str]) -> str:
    if not texts:
        return "No thesis available"
    joined = " ".join(texts).lower()
    key_phrases = ["earnings", "guidance", "ai", "valuation", "breakout", "momentum", "revenue", "catalyst"]
    matched = [p for p in key_phrases if p in joined]
    if matched:
        return f"Primary narrative: {', '.join(matched[:4])}."
    return "Primary narrative: momentum and trader attention."


def summarize_mentions(df: pd.DataFrame) -> pd.DataFrame:
    mentions: List[Mention] = []
    for _, row in df.iterrows():
        for ticker in extract_tickers(str(row.get("text", ""))):
            mentions.append(Mention(ticker=ticker, author=str(row.get("author", "unknown")), text=str(row.get("text", "")), timestamp=str(row.get("timestamp", ""))))

    grouped = defaultdict(list)
    for m in mentions:
        grouped[m.ticker].append(m)

    rows = []
    for ticker, group in grouped.items():
        sentiment_counts = Counter(infer_sentiment(m.text) for m in group)
        rows.append(
            {
                "Ticker": ticker,
                "Mentions": len(group),
                "Sentiment": sentiment_counts.most_common(1)[0][0],
                "Quick Thesis": make_thesis([m.text for m in group]),
                "Example Post": group[0].text,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["Ticker", "Mentions", "Sentiment", "Quick Thesis", "Example Post"])
    return pd.DataFrame(rows).sort_values(by="Mentions", ascending=False).reset_index(drop=True)


def load_feed() -> pd.DataFrame:
    if TWEETS_FILE.exists():
        return pd.read_csv(TWEETS_FILE)
    return pd.DataFrame(columns=["timestamp", "author", "text", "is_real_pitch"])


def main() -> None:
    st.set_page_config(page_title="Twitter Stock Radar", layout="wide")
    st.title("📈 X/Twitter List Stock Radar")
    st.caption("Curated-list workflow: fetch last 24h posts, filter noise, and rank stock pitches.")

    df = load_feed()
    summary = summarize_mentions(df)

    total_posts = len(df)
    total_mentions = int(df["text"].fillna("").str.count(TICKER_PATTERN).sum()) if total_posts else 0
    total_real_pitches = int(df["is_real_pitch"].sum()) if "is_real_pitch" in df.columns and total_posts else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total posts collected", total_posts)
    c2.metric("Total ticker mentions", total_mentions)
    c3.metric("Total real pitches", total_real_pitches)

    st.subheader("Ranked Dashboard")
    st.dataframe(summary, use_container_width=True)

    with st.expander("Raw tweets (last 24h after filters)"):
        st.dataframe(df, use_container_width=True)

    st.markdown("### Run data collection")
    st.code("python fetch_tweets.py", language="bash")


if __name__ == "__main__":
    main()
