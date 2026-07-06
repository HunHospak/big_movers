# big_movers

Independent ArkenLabs satellite service. Daily scan of a curated large/mid-cap universe for
big moves (|Δ| ≥ threshold), with an optional reason headline. Publishes one JSON feed that the
Arken research page consumes read-only.

## Output
`out/big_movers.json` — conforms to `schema.json` (the shared feed contract). Served statically
(GitHub Pages / Netlify) at a stable URL; Arken fetches it.

## Run locally
```bash
python -m venv .venv && . .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
export NEWS_API_KEY=...        # optional; without it status becomes "partial"
python src/build_feed.py       # writes out/big_movers.json + out/history/<date>.json
python scripts/post_text.py    # writes out/post.txt (ready-to-post snippet)
```

## Configure
`config.yaml`: threshold, min market cap, universe file, news provider, feed URL.
`universe.txt`: the tickers to scan (edit freely; one per line).

## Deploy
`.github/workflows/publish.yml` runs on a weekday cron, builds the feed, and publishes `out/`
to GitHub Pages. Set the repo secret `NEWS_API_KEY`. The feed then lives at
`https://<user>.github.io/big_movers/big_movers.json`.

## Status semantics
- `active` — price data present (and news enabled with a key, or news disabled).
- `partial` — movers computed, but no `NEWS_API_KEY` so reasons are missing.
- `unavailable` — no price data; Arken shows an "unavailable" card and is otherwise unaffected.

## Independence
This repo knows nothing about Arken. Arken knows only the feed URL + the shared schema. Either side
can change or die without breaking the other.
