# Can Tian's website

- `content.toml`: all text, papers, courses, art. The only file to edit.
- `static/`: style, PDFs (`static/files/`), photo and drawings (`static/img/`).
- `build.py`: `python3 build.py` regenerates `docs/` (the published site). Never edit `docs/` by hand.
- `SETUP.md`: one-time domain + GitHub setup.
- `_archive/`: the old Weebly pages (not published).

Plain HTML, no web fonts, no third-party scripts: fast, and loads in mainland China.
For search engines and AI agents: schema.org JSON-LD, Google Scholar `citation_*` tags on each paper page, `llms.txt`, `sitemap.xml`.
