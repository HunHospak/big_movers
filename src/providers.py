"""Data providers for big_movers — isolated so they can be swapped/mocked."""
from __future__ import annotations

from pathlib import Path

import requests
import yfinance as yf


def load_universe(path: str | Path) -> list[str]:
    tickers: list[str] = []
    seen: set[str] = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        s = line.strip().upper()
        if not s or s.startswith("#"):
            continue
        if s not in seen:
            seen.add(s)
            tickers.append(s)
    return tickers


def get_daily_moves(tickers: list[str]) -> list[dict]:
    """Best-effort [{ticker, name, prev_close, last, move_pct, market_cap}]."""
    if not tickers:
        return []
    data = yf.download(
        tickers, period="5d", interval="1d", group_by="ticker",
        auto_adjust=False, threads=True, progress=False,
    )
    rows: list[dict] = []
    multi = len(tickers) > 1
    for t in tickers:
        try:
            df = data[t] if multi else data
            closes = df["Close"].dropna()
            if len(closes) < 2:
                continue
            prev, last = float(closes.iloc[-2]), float(closes.iloc[-1])
            if prev <= 0:
                continue
            rows.append({
                "ticker": t,
                "name": t,
                "prev_close": round(prev, 4),
                "last": round(last, 4),
                "move_pct": round((last - prev) / prev * 100.0, 2),
                "market_cap": None,
            })
        except Exception:
            continue
    _attach_market_caps(rows)
    return rows


def _attach_market_caps(rows: list[dict]) -> None:
    for r in rows:
        try:
            fi = yf.Ticker(r["ticker"]).fast_info
            mc = None
            try:
                mc = fi["market_cap"]
            except Exception:
                mc = getattr(fi, "market_cap", None)
            if mc:
                r["market_cap"] = float(mc)
        except Exception:
            pass


def get_reason_headline(ticker: str, api_key: str | None) -> dict | None:
    """One recent headline for the ticker via newsapi.org. None if no key / no hit."""
    if not api_key:
        return None
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": f'"{ticker}"',
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 1,
                "apiKey": api_key,
            },
            timeout=10,
        )
        if r.status_code != 200:
            return None
        articles = r.json().get("articles") or []
        if not articles:
            return None
        a = articles[0]
        return {"title": a.get("title"), "url": a.get("url"), "published_at": a.get("publishedAt")}
    except Exception:
        return None
