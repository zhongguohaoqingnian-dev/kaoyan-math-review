#!/usr/bin/env python3
"""Embed data/papers-math2-2011-2026.json into client.js as PAPERS_MATH2."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "client.js"
DATA = ROOT / "data" / "papers-math2-2011-2026.json"
START = "    /* === PAPERS_MATH2_START === */\n"
END = "    /* === PAPERS_MATH2_END === */\n"


def main() -> None:
    papers = json.loads(DATA.read_text(encoding="utf-8"))
    payload = json.dumps(papers, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    block = START + "    const PAPERS_MATH2 = " + payload + ";\n" + END

    source = CLIENT.read_text(encoding="utf-8")
    if START in source and END in source:
        before, rest = source.split(START, 1)
        _, after = rest.split(END, 1)
        source = before + block + after
    else:
        anchor = "    /* === PAPERS_DATA_END === */\n"
        if anchor not in source:
            raise SystemExit("anchor not found")
        source = source.replace(anchor, anchor + "\n" + block, 1)

    if "const PAPERS_ALL = PAPERS.concat(PAPERS_MATH2);" not in source:
        source = source.replace(
            END,
            END
            + '\n    PAPERS.forEach((paper) => { paper.subject = "数一"; });\n'
            + '    PAPERS_MATH2.forEach((paper) => { paper.subject = "数二"; });\n'
            + "    const PAPERS_ALL = PAPERS.concat(PAPERS_MATH2);\n",
            1,
        )

    CLIENT.write_text(source, encoding="utf-8")
    print(
        f"embedded {len(papers)} Math II papers into {CLIENT} "
        f"({CLIENT.stat().st_size / 1024:.1f} KiB)"
    )


if __name__ == "__main__":
    main()
