# X/Twitter List Stock Radar

This project now uses a **curated X/Twitter list workflow** rather than manual dashboard text entry.

## Files
- `accounts.txt`: list of handles to track, one per line
- `raw_tweets.txt`: manual-mode input dump (for now)
- `fetch_tweets.py`: collects and filters posts from last 24h
- `tweets_last24h.csv`: generated cleaned dataset for dashboard
- `app.py`: ranked dashboard and metrics

## Modes
1. **Manual mode (works now)**
   - Put tweet lines in `raw_tweets.txt` in this format:
     `2026-05-02T13:15:00Z|username|tweet text`
   - Run `python fetch_tweets.py`
2. **API mode placeholder**
   - `fetch_from_api_placeholder()` is included for adding X API credentials later

## Filters applied
- Keep only last 24h tweets
- Keep only usernames listed in `accounts.txt` (if file has entries)
- Deduplicate by `(author, normalized text)`
- Ignore ads, pure reposts, politics, and UI noise text

## Dashboard outputs
- total posts collected
- total ticker mentions
- total real pitches
- ranked dashboard by ticker mentions

## Run
```bash
pip install -r requirements.txt
python fetch_tweets.py
streamlit run app.py
```
