"""Pure logic — no I/O, easy to unit-test."""
from __future__ import annotations


def find_big_movers(rows: list[dict], min_cap: float, threshold: float) -> list[dict]:
    """Large-cap names whose |daily move| >= threshold, sorted by magnitude.

    Unknown market cap (None) is NOT excluded — the universe is curated large/mid caps,
    so a missing cap lookup should not drop a real mover.
    """
    movers: list[dict] = []
    for r in rows:
        if abs(r.get("move_pct", 0.0)) < threshold:
            continue
        cap = r.get("market_cap")
        if min_cap and cap is not None and cap < min_cap:
            continue
        movers.append(r)
    movers.sort(key=lambda r: -abs(r.get("move_pct", 0.0)))
    return movers
