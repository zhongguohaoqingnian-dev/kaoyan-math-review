#!/usr/bin/env python3
"""Embed data/papers-2011-2026.json into client.js as the PAPERS constant."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "client.js"
DATA = ROOT / "data" / "papers-2011-2026.json"
START = "    /* === PAPERS_DATA_START === */\n"
END = "    /* === PAPERS_DATA_END === */\n"


def main() -> None:
    papers = json.loads(DATA.read_text(encoding="utf-8"))
    payload = json.dumps(papers, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    block = START + "    const PAPERS = " + payload + ";\n" + END

    source = CLIENT.read_text(encoding="utf-8")
    if START in source and END in source:
        before, rest = source.split(START, 1)
        _, after = rest.split(END, 1)
        source = before + block + after
    else:
        anchor = "    const h = React.createElement;\n"
        if anchor not in source:
            raise SystemExit("anchor not found")
        source = source.replace(anchor, anchor + "\n" + block, 1)

    CLIENT.write_text(source, encoding="utf-8")
    print(
        f"embedded {len(papers)} papers into {CLIENT} "
        f"({CLIENT.stat().st_size / 1024:.1f} KiB)"
    )


if __name__ == "__main__":
    main()
