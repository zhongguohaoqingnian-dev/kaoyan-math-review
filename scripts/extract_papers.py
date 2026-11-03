#!/usr/bin/env python3
"""Extract the 2011-2026 数学一 papers from 数一学习OS-海岛版.

The source is the island's SQLite library (read-only).  Output is a compact
JSON document with sections, question stems, short answers, solutions and the
one embedded figure.  LaTeX is sanitized to the subset rendered by the plugin.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sqlite3
from pathlib import Path

DEFAULT_DB = Path("/Users/chenchenyanji/Desktop/数一学习OS-海岛版/data/mathos.sqlite")
DEFAULT_ROOT = Path("/Users/chenchenyanji/Desktop/数一学习OS-海岛版")

NO_ARG_REMOVE = {
    "displaystyle", "textstyle", "scriptstyle", "scriptscriptstyle",
    "limits", "nolimits", "big", "Big", "bigg", "Bigg",
    "bigl", "bigr", "Bigl", "Bigr", "biggl", "biggr",
    "hline", "not", "centernot", "allowbreak", "nonumber", "notag",
}
STRIP_WRAPPERS = {
    "boxed", "pmb", "boldsymbol", "mathbf", "mathbb", "mathcal", "mathscr",
    "underbrace", "overbrace", "mathop", "mathrel", "phantom", "hphantom",
    "vphantom", "hspace", "vspace", "label", "ref",
}
KEEP_WRAPPERS = {
    "overline", "underline", "hat", "widehat", "bar", "vec", "overrightarrow",
    "frac", "dfrac", "tfrac", "sqrt", "mathrm", "text", "textbf", "operatorname",
    "left", "right",
}
TWO_ARG_STRIP = {"overset", "stackrel", "underset"}
X_ARROWS = {"xrightarrow": "→", "xleftarrow": "←", "xlongequal": "="}
COLOR_COMMANDS = {"color"}


def read_group(s: str, i: int):
    """Read a balanced {...} group starting at s[i] == '{'."""
    if i >= len(s) or s[i] != "{":
        return "", i
    depth = 1
    j = i + 1
    start = j
    while j < len(s):
        ch = s[j]
        if ch == "\\":
            j += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start:j], j + 1
        j += 1
    return s[start:], len(s)


def skip_space(s: str, i: int) -> int:
    while i < len(s) and s[i].isspace():
        i += 1
    return i


def sanitize(s: str) -> str:
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue

        j = i + 1
        if j >= n:
            out.append("\\")
            break
        if not s[j].isalpha():
            # control symbol: \\, \{, \%, \ , etc.
            out.append(s[i:j + 1])
            i = j + 1
            continue

        name_start = j
        while j < n and s[j].isalpha():
            j += 1
        name = s[name_start:j]

        if name in NO_ARG_REMOVE:
            i = j
            continue

        k = skip_space(s, j)
        if name in STRIP_WRAPPERS:
            if k < n and s[k] == "{":
                content, end = read_group(s, k)
                out.append(sanitize(content))
                i = end
            else:
                i = j
            continue

        if name in KEEP_WRAPPERS:
            if k < n and s[k] == "{":
                content, end = read_group(s, k)
                out.append("\\" + name + "{" + sanitize(content) + "}")
                i = end
            else:
                out.append("\\" + name)
                i = j
            continue

        if name == "binom":
            if k < n and s[k] == "{":
                a, end = read_group(s, k)
                k2 = skip_space(s, end)
                if k2 < n and s[k2] == "{":
                    b, end2 = read_group(s, k2)
                    out.append(
                        "\\left(\\begin{array}{c}" + sanitize(a) + "\\\\" +
                        sanitize(b) + "\\end{array}\\right)"
                    )
                    i = end2
                    continue
            i = j
            continue

        if name == "substack":
            if k < n and s[k] == "{":
                content, end = read_group(s, k)
                out.append("\\begin{gathered}" + sanitize(content) + "\\end{gathered}")
                i = end
            else:
                i = j
            continue

        if name in TWO_ARG_STRIP:
            if k < n and s[k] == "{":
                _, end = read_group(s, k)
                k2 = skip_space(s, end)
                if k2 < n and s[k2] == "{":
                    base, end2 = read_group(s, k2)
                    out.append(sanitize(base))
                    i = end2
                    continue
            i = j
            continue

        if name in X_ARROWS:
            if k < n and s[k] == "{":
                _, end = read_group(s, k)
                out.append(X_ARROWS[name])
                i = end
            else:
                out.append(X_ARROWS[name])
                i = j
            continue

        if name in COLOR_COMMANDS:
            if k < n and s[k] == "{":
                _, end = read_group(s, k)
                i = end
            else:
                i = j
            continue

        if name == "textcolor":
            if k < n and s[k] == "{":
                _, end = read_group(s, k)
                k2 = skip_space(s, end)
                if k2 < n and s[k2] == "{":
                    body, end2 = read_group(s, k2)
                    out.append(sanitize(body))
                    i = end2
                    continue
            i = j
            continue

        if name in ("tag", "label", "ref"):
            if k < n and s[k] == "{":
                _, end = read_group(s, k)
                i = end
            else:
                i = j
            continue

        if name == "pmod":
            if k < n and s[k] == "{":
                content, end = read_group(s, k)
                out.append("\\quad(\\mathrm{mod}\\ " + sanitize(content) + ")")
                i = end
            else:
                i = j
            continue

        # Keep the command and continue scanning its arguments.
        out.append("\\" + name)
        i = j

    return "".join(out).replace("\u2028", " ").replace("\u2029", " ")


def first_line_answer(solution: str) -> str:
    if not solution:
        return ""
    line = solution.strip().splitlines()[0].strip()
    line = re.sub(r"^\*\*答案[：:]\s*", "", line)
    line = re.sub(r"^\*\*答案\*\*\s*", "", line)
    line = re.sub(r"^答案[：:]\s*", "", line)
    line = line.replace("**", "").strip()
    if not line or line.startswith("解答"):
        return ""
    # Prefer the first sentence/answer, but keep short formulas intact.
    if len(line) > 180:
        line = line[:180].rstrip() + "…"
    return line


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--subject", default="数学一")
    parser.add_argument("--tag", default="数一")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "papers-2011-2026.json")
    args = parser.parse_args()

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    papers = con.execute(
        """
        SELECT id, year, title, total_score, duration_minutes
        FROM exam_papers
        WHERE subject LIKE ?
          AND year BETWEEN 2011 AND 2026
          AND title LIKE '%全国硕士研究生招生考试%'
          AND deleted_at IS NULL
        ORDER BY year DESC
        """,
        (f"%{args.subject}%",),
    ).fetchall()

    output = []
    for paper in papers:
        paper_id = paper["id"]
        sections = con.execute(
            """
            SELECT id, title, sort_order
            FROM exam_paper_sections
            WHERE paper_id = ? AND deleted_at IS NULL
            ORDER BY sort_order, id
            """,
            (paper_id,),
        ).fetchall()
        questions = con.execute(
            """
            SELECT pq.display_no, pq.points, pq.sort_order, q.id AS qid, q.content_md
            FROM exam_paper_questions pq
            JOIN questions q ON q.id = pq.question_id
            WHERE pq.paper_id = ? AND pq.deleted_at IS NULL AND q.deleted_at IS NULL
            ORDER BY pq.sort_order, pq.id
            """,
            (paper_id,),
        ).fetchall()

        q_by_section = {}
        for question in questions:
            section = con.execute(
                """
                SELECT s.id, s.title
                FROM exam_paper_questions pq
                JOIN exam_paper_sections s ON s.id = pq.section_id
                WHERE pq.paper_id = ? AND pq.display_no = ?
                  AND pq.deleted_at IS NULL AND s.deleted_at IS NULL
                LIMIT 1
                """,
                (paper_id, question["display_no"]),
            ).fetchone()
            key = section["id"] if section else "none"
            q_by_section.setdefault(key, []).append(question)

        section_meta = {s["id"]: s for s in sections}
        section_meta["none"] = {"id": "none", "title": "试题"}

        built_sections = []
        for key in sorted(q_by_section, key=lambda k: 0 if k == "none" else section_meta[k]["sort_order"]):
            sec = section_meta[key]
            built_questions = []
            for question in q_by_section[key]:
                qid = question["qid"]
                solutions = con.execute(
                    """
                    SELECT title, content_md
                    FROM solutions
                    WHERE question_id = ? AND deleted_at IS NULL
                    ORDER BY ordinal, id
                    """,
                    (qid,),
                ).fetchall()
                solution_parts = []
                for sol in solutions:
                    body = sanitize(sol["content_md"]).strip()
                    if body:
                        solution_parts.append(body)
                solution = "\n\n---\n\n".join(solution_parts)
                answer = first_line_answer(sanitize(solutions[0]["content_md"]) if solutions else "")

                stem = sanitize(question["content_md"]).strip()
                images = []
                asset_rows = con.execute(
                    """
                    SELECT qa.alt_text, m.rel_path, m.mime_type
                    FROM question_assets qa
                    JOIN media_assets m ON m.id = qa.asset_id
                    WHERE qa.question_id = ? AND qa.deleted_at IS NULL AND m.deleted_at IS NULL
                    ORDER BY qa.sort_order, qa.id
                    """,
                    (qid,),
                ).fetchall()
                for asset in asset_rows:
                    path = args.root / asset["rel_path"]
                    if not path.exists() or not asset["mime_type"].startswith("image/"):
                        continue
                    raw = path.read_bytes()
                    if len(raw) > 600_000:
                        continue
                    images.append(
                        {
                            "alt": asset["alt_text"] or "题目配图",
                            "src": "data:" + asset["mime_type"] + ";base64,"
                            + base64.b64encode(raw).decode("ascii"),
                        }
                    )
                # Remove markdown image references; the structured image renders instead.
                stem = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", stem).strip()

                built_questions.append(
                    {
                        "no": question["display_no"],
                        "points": question["points"],
                        "stem": stem,
                        "answer": answer,
                        "solution": solution,
                        "images": images,
                    }
                )
            built_sections.append(
                {
                    "title": sec["title"],
                    "questions": built_questions,
                }
            )

        output.append(
            {
                "subject": args.tag,
                "year": paper["year"],
                "title": paper["title"],
                "total": paper["total_score"],
                "duration": paper["duration_minutes"],
                "questionCount": len(questions),
                "sections": built_sections,
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    size = args.out.stat().st_size
    questions = sum(len(s["questions"]) for p in output for s in p["sections"])
    print(f"wrote {args.out} ({size/1024:.1f} KiB), papers={len(output)}, questions={questions}")


if __name__ == "__main__":
    main()
