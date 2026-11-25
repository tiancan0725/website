#!/usr/bin/env python3
"""Tell Bing (and other IndexNow engines) that pages changed. Run AFTER pushing:  python3 indexnow.py
Sends every URL in docs/sitemap.xml. The key file docs/<key>.txt must already be live on the site."""
import json, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
key = (ROOT / ".indexnow-key").read_text().strip()
urls = re.findall(r"<loc>([^<]+)</loc>", (ROOT / "docs" / "sitemap.xml").read_text())
body = json.dumps({"host": "tiancan.org", "key": key,
                   "keyLocation": f"https://tiancan.org/{key}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                             headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req) as r:
    print(r.status, f"submitted {len(urls)} URLs")  # 200 or 202 = accepted
