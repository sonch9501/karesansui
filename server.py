#!/usr/bin/env python3
"""karesansui — your markdown journal, rendered as a zen rock garden.

Zero dependencies. Python standard library only.

Usage:
    python3 server.py [ROOT_DIR] [--port PORT] [--no-browser]

ROOT_DIR defaults to ./sample so the garden works right after cloning.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))

DATE_RE = re.compile(r"(\d{4})-?(\d{2})-?(\d{2})")
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".obsidian", ".claude"}
SKIP_FILES = {"_template.md"}


def parse_frontmatter(text):
    """Tiny YAML-ish frontmatter parser: key: value pairs and [a, b] lists."""
    meta = {}
    if not text.startswith("---"):
        return meta, text
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    block = text[3:end]
    body = text[end + 4:]
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip("'\"") for v in value[1:-1].split(",")]
            meta[key] = [v for v in items if v]
        else:
            meta[key] = value.strip("'\"")
    return meta, body


def extract_date(meta, filename):
    for source in (str(meta.get("date", "")), filename):
        m = DATE_RE.search(source)
        if m:
            y, mo, d = m.groups()
            if 1900 < int(y) < 2200 and 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
                return f"{y}-{mo}-{d}"
    return None


def extract_title(body, filename):
    m = H1_RE.search(body)
    if m:
        return m.group(1).strip()
    name = os.path.splitext(filename)[0]
    return re.sub(r"^[\d_\-]+", "", name) or name


def extract_excerpt(body, limit=140):
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "---", "|", "```", "<", "![")):
            continue
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"[*_`\[\]()>]", "", line)
        if line:
            return line[:limit]
    return ""


def scan(root):
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn in SKIP_FILES:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            meta, body = parse_frontmatter(text)
            top = rel.split(os.sep)[0] if os.sep in rel else "."
            category = str(meta.get("category") or (top if top != "." else "notes"))
            entries.append({
                "id": hashlib.sha1(rel.encode("utf-8")).hexdigest()[:12],
                "path": rel.replace(os.sep, "/"),
                "title": extract_title(body, fn),
                "date": extract_date(meta, fn),
                "category": category,
                "tags": meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
                "size": len(body),
                "meta": fn.startswith("_"),
                "excerpt": extract_excerpt(body),
            })
    return entries


class Handler(BaseHTTPRequestHandler):
    root = None  # set at startup

    def _send(self, code, payload, content_type="application/json; charset=utf-8"):
        data = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif parsed.path == "/api/garden":
            entries = scan(self.root)
            seed = int(hashlib.sha1(os.path.abspath(self.root).encode()).hexdigest()[:8], 16)
            self._send(200, {
                "root": os.path.basename(os.path.abspath(self.root)) or self.root,
                "seed": seed,
                "entries": entries,
            })
        elif parsed.path == "/api/file":
            rel = parse_qs(parsed.query).get("path", [""])[0]
            full = os.path.realpath(os.path.join(self.root, rel))
            if not (full + os.sep).startswith(os.path.realpath(self.root) + os.sep) or not full.endswith(".md"):
                self._send(403, {"error": "forbidden"})
                return
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    self._send(200, {"path": rel, "content": f.read()})
            except OSError:
                self._send(404, {"error": "not found"})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):  # quiet
        pass


def main():
    ap = argparse.ArgumentParser(description="karesansui — markdown zen garden")
    ap.add_argument("root", nargs="?", default=os.path.join(HERE, "sample"),
                    help="directory containing your .md files (default: ./sample)")
    ap.add_argument("--port", type=int, default=8737)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.root))
    if not os.path.isdir(root):
        sys.exit(f"error: not a directory: {root}")

    Handler.root = root
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    n = len(scan(root))
    print(f"karesansui ⛰  {n} stones in the garden")
    print(f"  root : {root}")
    print(f"  url  : {url}")
    if not args.no_browser:
        threading.Timer(0.4, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nthe garden rests.")


if __name__ == "__main__":
    main()
