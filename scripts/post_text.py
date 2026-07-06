"""Generate a ready-to-post social snippet from the latest feed."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    feed = json.loads((ROOT / "out" / "big_movers.json").read_text(encoding="utf-8"))
    d = feed["data"]
    ups = [m for m in d["movers"] if m["move_pct"] > 0][:3]
    downs = [m for m in d["movers"] if m["move_pct"] < 0][:3]

    lines = [f"Big movers — {d['as_of']} (large caps)"]
    for m in ups:
        r = f" — {m['reason']}" if m.get("reason") else ""
        lines.append(f"▲ ${m['ticker']} +{m['move_pct']:.1f}%{r}")
    for m in downs:
        r = f" — {m['reason']}" if m.get("reason") else ""
        lines.append(f"▼ ${m['ticker']} {m['move_pct']:.1f}%{r}")
    lines.append("Not investment advice · arkenlabs.eu")

    text = "\n".join(lines)
    (ROOT / "out" / "post.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
