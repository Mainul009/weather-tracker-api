"""Builds two printable HTML files from the project:
  code_listing.html      every .py file with line numbers
  endpoint_summary.html  the endpoint table taken from README.md

Run from the project root:  python make_pdfs.py
Then open each HTML file in Chrome or Edge, press Ctrl+P and choose Save as PDF.
"""
import html
import os

SKIP_DIRS = {"venv", "__pycache__", ".git", "node_modules", "submission"}
ROOT = os.path.dirname(os.path.abspath(__file__))

STYLE = """
<style>
  body { font-family: Arial, sans-serif; margin: 24px; }
  h1 { font-size: 20px; }
  h2 { font-size: 14px; background: #eee; padding: 6px; margin-top: 28px; page-break-before: always; }
  h2.first { page-break-before: auto; }
  pre { font-family: Consolas, monospace; font-size: 10px; line-height: 1.35; white-space: pre-wrap; word-wrap: break-word; }
  .ln { color: #888; user-select: none; }
  table { border-collapse: collapse; width: 100%; font-size: 10px; }
  th, td { border: 1px solid #999; padding: 4px; text-align: left; vertical-align: top; }
  th { background: #ddd; }
</style>
"""


def python_files():
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if name.endswith(".py") and name != os.path.basename(__file__):
                found.append(os.path.join(folder, name))
    # app.py first, then the rest in folder order
    found.sort(key=lambda p: (os.path.relpath(p, ROOT) != "app.py", os.path.relpath(p, ROOT)))
    return found


def build_code_listing():
    parts = ["<html><head><meta charset='utf-8'><title>Code listing</title>", STYLE, "</head><body>",
             "<h1>Weather Forecast Tracker API: complete code listing</h1>"]
    empty = []
    shown = 0
    for path in python_files():
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        if not lines:
            empty.append(rel)
            continue
        cls = "first" if shown == 0 else ""
        shown += 1
        parts.append(f"<h2 class='{cls}'>{html.escape(rel)} ({len(lines)} lines)</h2><pre>")
        for n, line in enumerate(lines, 1):
            parts.append(f"<span class='ln'>{n:>4}  </span>{html.escape(line)}")
        parts.append("</pre>")
    if empty:
        parts.append("<h2>Empty files</h2><pre>" + html.escape("\n".join(empty)) + "</pre>")
    parts.append("</body></html>")
    with open(os.path.join(ROOT, "code_listing.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("Wrote code_listing.html")


def build_endpoint_summary():
    readme = os.path.join(ROOT, "README.md")
    if not os.path.exists(readme):
        print("README.md not found, skipped endpoint summary")
        return
    rows, inside = [], False
    with open(readme, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## Endpoint summary"):
                inside = True
                continue
            if inside and line.startswith("#"):
                break
            if inside and line.strip().startswith("|"):
                rows.append([c.strip().replace("`", "") for c in line.strip().strip("|").split("|")])
    rows = [r for r in rows if not set("".join(r)) <= set("-: ")]  # drop the --- separator row
    if not rows:
        print("No table found under '## Endpoint summary' in README.md")
        return
    out = ["<html><head><meta charset='utf-8'><title>Endpoint summary</title>", STYLE, "</head><body>",
           "<h1>Weather Forecast Tracker API: endpoint summary</h1>",
           "<p>Base URL: http://127.0.0.1:5001/api/v1</p><table>"]
    for i, r in enumerate(rows):
        tag = "th" if i == 0 else "td"
        out.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in r) + "</tr>")
    out.append("</table></body></html>")
    with open(os.path.join(ROOT, "endpoint_summary.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Wrote endpoint_summary.html ({len(rows) - 1} endpoints)")


if __name__ == "__main__":
    build_code_listing()
    build_endpoint_summary()
