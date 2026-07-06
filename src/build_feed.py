"""Orchestration: ingest -> compute -> validate(schema) -> write out/."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Load secrets from a local .env (gitignored) if present. In CI, the same env vars
# come from repo secrets instead — the code path is identical (os.environ).
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass

from providers import get_daily_moves, get_reason_headline, load_universe  # noqa: E402
from compute import find_big_movers  # noqa: E402

MOVER_FIELDS = ("ticker", "name", "move_pct", "last", "market_cap", "reason", "reason_url")


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def load_schema() -> dict:
    return json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))


def build(cfg: dict) -> dict:
    universe = load_universe(ROOT / cfg["universe_file"])
    rows = get_daily_moves(universe)
    movers = find_big_movers(rows, cfg.get("min_market_cap_usd", 0), cfg["move_threshold_pct"])

    news = cfg.get("news", {}) or {}
    api_key = os.environ.get(news.get("api_key_env", "")) if news.get("enabled") else None
    if news.get("enabled"):
        for m in movers[: int(news.get("max_movers_enriched", 25))]:
            h = get_reason_headline(m["ticker"], api_key)
            m["reason"] = h["title"] if h else None
            m["reason_url"] = h["url"] if h else None
    for m in movers:
        m.setdefault("reason", None)
        m.setdefault("reason_url", None)

    if not rows:
        status, notes = "unavailable", "no price data"
    elif news.get("enabled") and not api_key:
        status, notes = "partial", "no NEWS_API_KEY: movers shown without reason headlines"
    else:
        status, notes = "active", None

    feed = {
        "service": cfg["service"],
        "schema_version": str(cfg["schema_version"]),
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "ttl_hours": cfg["ttl_hours"],
        "data": {
            "as_of": dt.date.today().isoformat(),
            "count": len(movers),
            "movers": [{k: m.get(k) for k in MOVER_FIELDS} for m in movers],
        },
    }
    if notes:
        feed["notes"] = notes
    return feed


def main() -> None:
    cfg = load_config()
    feed = build(cfg)
    jsonschema.validate(feed, load_schema())

    out = ROOT / "out"
    (out / "history").mkdir(parents=True, exist_ok=True)
    payload = json.dumps(feed, indent=2)
    (out / "big_movers.json").write_text(payload, encoding="utf-8")
    (out / "history" / f"{feed['data']['as_of']}.json").write_text(payload, encoding="utf-8")
    print(f"[big_movers] status={feed['status']} movers={feed['data']['count']}")


if __name__ == "__main__":
    main()
