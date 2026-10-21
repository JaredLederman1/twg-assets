"""Pick N least-recently-used backgrounds, spread across themes, and mark them used.

Usage: python3 pipeline/pick_backgrounds.py N YYYY-MM-DD
Prints one repo-relative path per line and updates backgrounds.csv in place.
"""
import csv, pathlib, random, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "backgrounds.csv"


def main(n, today):
    rows = list(csv.DictReader(MANIFEST.open()))
    rows = [r for r in rows if (REPO / r["file"]).exists()]
    random.shuffle(rows)
    rows.sort(key=lambda r: r["last_used"] or "")  # never-used first, then oldest
    picked, themes_used = [], {}
    # round-robin over themes among the least-recently-used candidates
    pool = rows[: max(n * 3, n)]
    while len(picked) < n and pool:
        pool.sort(key=lambda r: (themes_used.get(r["theme"], 0), r["last_used"] or ""))
        r = pool.pop(0)
        picked.append(r)
        themes_used[r["theme"]] = themes_used.get(r["theme"], 0) + 1
    for r in picked:
        r["last_used"] = today
    all_rows = {r["file"]: r for r in csv.DictReader(MANIFEST.open())}
    for r in picked:
        all_rows[r["file"]]["last_used"] = today
    with MANIFEST.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "theme", "last_used"])
        w.writeheader(); w.writerows(all_rows.values())
    random.shuffle(picked)
    for r in picked:
        print(r["file"])


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2])
