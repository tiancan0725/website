#!/usr/bin/env python3
"""Build the site: content.toml + static/ -> docs/ (served by GitHub Pages).

Usage:  python3 build.py
Everything you'd ever edit lives in content.toml. This script turns it into plain HTML,
plus the files that search engines and AI agents read (sitemap.xml, robots.txt, llms.txt,
schema.org JSON-LD, Google Scholar citation_* tags). No dependencies beyond Python 3.11+.
"""
import hashlib, html, json, shutil, tomllib, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
C = tomllib.loads((ROOT / "content.toml").read_text(encoding="utf-8"))
S = C["site"]
BASE = S.get("base_url", "").rstrip("/")
TODAY = dt.date.today().isoformat()
CSS_V = hashlib.md5((ROOT / "static" / "style.css").read_bytes()).hexdigest()[:8]
e = lambda s: html.escape(str(s), quote=True)


def absu(path):
    """Absolute URL when the domain is known, else site-root-relative."""
    return f"{BASE}{path}" if BASE else path


def write(path, text):
    p = OUT / path.lstrip("/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


NAV = [("/", "Home"), ("/research/", "Research"), ("/teaching/", "Teaching"),
       ("/cv/", "CV"), ("/life/", "Life"), ("/zh/", "中文")]


def page(path, title, body, description, extra_head="", lang="en", og_type="website"):
    nav = "".join(
        f'<li><a href="{u}"{" aria-current=\"page\"" if (u == path or (u != "/" and path.startswith(u))) else ""}>{t}</a></li>'
        for u, t in NAV)
    hreflang = (f'<link rel="alternate" hreflang="en" href="{absu("/")}">'
                f'<link rel="alternate" hreflang="zh-CN" href="{absu("/zh/")}">') if path in ("/", "/zh/") else ""
    full_title = title if title == S["name"] else f"{title} · {S['name']}"
    canon = f'<link rel="canonical" href="{absu(path)}">' if BASE else ""
    og_img = f'<meta property="og:image" content="{absu("/img/can-tian.jpg")}">' if BASE else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<meta name="author" content="{e(S['name'])}">
{canon}
<meta property="og:type" content="{og_type}">
{hreflang}
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
{og_img}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/style.css?v={CSS_V}">
<link rel="alternate" type="text/plain" href="/llms.txt" title="Plain-text summary for language models">
{extra_head}
</head>
<body>
<header class="site"><div class="wrap">
<a class="brand" href="/">{e(S['name'])} <span lang="zh-CN">{e(S['name_zh'])}</span></a>
<nav aria-label="Main"><ul>{nav}</ul></nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer class="site"><div class="wrap">
{e(S['name'])} · {e(S['position'])}, {e(S['department'])}, {e(S['institution'])} ·
<a href="mailto:{e(S['email'])}">{e(S['email'])}</a> · updated {TODAY}
</div></footer>
</body>
</html>
"""


# ---------- people & papers ----------
PEOPLE = C.get("people", {})


def person(name, link=True):
    url = PEOPLE.get(name)
    return f'<a href="{e(url)}">{e(name)}</a>' if (url and link) else e(name)


def coauthors(p, link=True):
    others = [a for a in p["authors"] if a != S["name"]]
    if not others:
        return ""
    names = [person(a, link) for a in others]
    joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    return f"with {joined}"


def venue_line(p):
    if p["kind"] == "published":
        bits = [f"<em>{e(p['journal'])}</em>"]
        if p.get("volume"): bits.append(f"vol. {e(p['volume'])}" + (f"({e(p['issue'])})" if p.get("issue") else ""))
        if p.get("pages"): bits.append(f"pp. {e(p['pages'])}")
        if p.get("article"): bits.append(f"art. {e(p['article'])}")
        bits.append(e(p["year"]))
        return ", ".join(bits)
    return e(p.get("status", "Working paper"))


def paper_links(p):
    out = []
    if p.get("pdf"): out.append(f'<a href="/files/{e(p["pdf"])}">{e(p.get("pdf_label", "PDF"))}</a>')
    if p.get("doi") and p["kind"] == "published": out.append(f'<a href="https://doi.org/{e(p["doi"])}">Journal version</a>')
    for l in p.get("links", []):
        href = l["url"] if "://" in l["url"] else f"/files/{l['url']}"
        out.append(f'<a href="{e(href)}">{e(l["label"])}</a>')
    return out


def paper_item(p):
    co = coauthors(p)
    acts = paper_links(p) + [f'<a href="/papers/{p["slug"]}/">Abstract &amp; BibTeX</a>']
    abstract = (f'<details><summary>Abstract</summary><p>{e(p["abstract"])}</p></details>'
                if p.get("abstract") else "")
    return f"""<article class="paper">
<h3><a href="/papers/{p['slug']}/">{e(p['title'])}</a></h3>
<p class="meta">{co + ' · ' if co else ''}{('<span class="status">' + venue_line(p) + '</span>') if p['kind'] != 'published' else venue_line(p)}</p>
{('<p class="question">' + e(p['question']) + '</p>') if p.get('question') else ''}
<p class="actions">{' '.join(acts)}</p>
{abstract}
</article>"""


def authors_line(p):
    names = [person(a) for a in p["authors"]]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def bibtex(p):
    key = p["authors"][0].split()[-1].lower() + str(p.get("year", "")) + p["slug"].split("-")[0]
    auth = " and ".join(f"{a.split()[-1]}, {' '.join(a.split()[:-1])}" for a in p["authors"])
    if p["kind"] == "published":
        f = [("title", p["title"]), ("author", auth), ("journal", p["journal"]), ("year", p["year"]),
             ("volume", p.get("volume")), ("number", p.get("issue")),
             ("pages", (p.get("pages") or "").replace("-", "--") or p.get("article")), ("doi", p.get("doi"))]
        typ = "article"
    else:
        f = [("title", p["title"]), ("author", auth), ("year", p.get("year")),
             ("institution", p.get("series")), ("number", p.get("number")), ("type", p.get("series_type")),
             ("doi", p.get("doi")), ("url", absu(f"/papers/{p['slug']}/")),
             ("note", None if p.get("series") else "Working paper")]
        typ = "techreport" if p.get("series") else "unpublished"
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in f if v)
    return f"@{typ}{{{key},\n{body}\n}}"


def scholar_meta(p):
    m = [("citation_title", p["title"])] + [("citation_author", a) for a in p["authors"]]
    if p.get("year"): m.append(("citation_publication_date", str(p["year"])))
    if p["kind"] == "published":
        m += [("citation_journal_title", p["journal"]), ("citation_volume", p.get("volume")),
              ("citation_issue", p.get("issue")), ("citation_doi", p.get("doi"))]
        if p.get("pages"):
            a, _, b = p["pages"].partition("-")
            m += [("citation_firstpage", a), ("citation_lastpage", b)]
        elif p.get("article"):
            m.append(("citation_firstpage", p["article"]))
    else:
        if p.get("series"): m.append(("citation_technical_report_institution", p["series"]))
        if p.get("number"): m.append(("citation_technical_report_number", p["number"]))
    if p.get("pdf"): m.append(("citation_pdf_url", absu(f"/files/{p['pdf']}")))
    tags = "\n".join(f'<meta name="{k}" content="{e(v)}">' for k, v in m if v)
    ld = {"@context": "https://schema.org", "@type": "ScholarlyArticle", "headline": p["title"],
          "name": p["title"], "author": [{"@type": "Person", "name": a, **({"url": PEOPLE[a]} if a in PEOPLE else {})}
                                          for a in p["authors"]],
          "url": absu(f"/papers/{p['slug']}/")}
    if p.get("abstract"): ld["abstract"] = p["abstract"]
    if p.get("question"): ld["description"] = p["question"]
    if p.get("year"): ld["datePublished"] = p.get("date") or str(p["year"])
    if p.get("doi"): ld["sameAs"] = f"https://doi.org/{p['doi']}"; ld["identifier"] = {"@type": "PropertyValue", "propertyID": "DOI", "value": p["doi"]}
    if p["kind"] == "published": ld["isPartOf"] = {"@type": "Periodical", "name": p["journal"]}
    if p.get("keywords"): ld["keywords"] = p["keywords"]
    return tags + f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'


def paper_page(p):
    co = coauthors(p)
    acts = paper_links(p)
    bib = bibtex(p)
    abstract = f'<h2>Abstract</h2><p class="abstract">{e(p["abstract"])}</p>' if p.get("abstract") else ""
    notes = "".join(f"<p class='small muted'>{e(n)}</p>" for n in p.get("notes", []))
    body = f"""<p class="small"><a href="/research/">← Research</a></p>
<h1>{e(p['title'])}</h1>
<p class="meta">{authors_line(p)}</p>
<p class="meta">{('<span class="status">' + venue_line(p) + '</span>') if p['kind'] != 'published' else venue_line(p)}</p>
<p class="actions">{' '.join(acts)}</p>
{notes}
{('<h2>The question</h2><p class="abstract">' + e(p['question']) + '</p>') if p.get('question') else ''}
{abstract}
<h2>Cite</h2>
<pre class="bib" id="bib">{e(bib)}</pre>
<button class="copy" type="button" onclick="navigator.clipboard.writeText(document.getElementById('bib').innerText).then(()=>{{this.textContent='Copied'}}).catch(()=>{{this.textContent='Select the text above to copy'}})">Copy BibTeX</button>"""
    desc = " ".join(x for x in (p.get("question"), p.get("abstract")) if x) or f"{p['title']}, by {', '.join(p['authors'])}."
    if len(desc) > 300: desc = desc[:300].rsplit(" ", 1)[0] + "…"
    return page(f"/papers/{p['slug']}/", p["title"], body, desc, scholar_meta(p), og_type="article")


PAPERS = C["papers"]
WORKING = [p for p in PAPERS if p["kind"] == "working"]
PUBLISHED = [p for p in PAPERS if p["kind"] == "published"]


# ---------- pages ----------
def home():
    links = "".join(f'<li><a href="{e(l["url"])}">{e(l["label"])}</a></li>' for l in C["profile_links"] if l.get("url"))
    tags = "".join(f"<li>{e(t[0].upper() + t[1:])}</li>" for t in S["interests"])
    body = f"""<section class="intro">
<img src="/img/can-tian.jpg" width="600" height="750" alt="Portrait of {e(S['name'])}">
<div>
<h1>{e(S['name'])} <span class="muted" lang="zh-CN">{e(S['name_zh'])}</span></h1>
<div class="title">{e(S['position'])}, {e(S['department'])}<br>{e(S['institution'])}</div>
{S['bio_html']}
<ul class="tags" aria-label="Research interests">{tags}</ul>
<p class="pron">{S['pronunciation_html']}</p>
<p class="small">
<a href="mailto:{e(S['email'])}">{e(S['email'])}</a> · <a href="mailto:{e(S['email_alt'])}">{e(S['email_alt'])}</a><br>
<span class="muted">{e(S['address'])}</span></p>
<ul class="links">{links}</ul>
</div>
</section>"""
    person_ld = {
        "@context": "https://schema.org", "@type": "Person", "name": S["name"],
        "alternateName": [S["name_zh"]], "givenName": "Can", "familyName": "Tian",
        "jobTitle": S["position"], "email": f"mailto:{S['email']}",
        "worksFor": {"@type": "CollegeOrUniversity", "name": S["institution"],
                     "department": {"@type": "Organization", "name": S["department"]}},
        "alumniOf": [{"@type": "CollegeOrUniversity", "name": n} for n in S["alumni"]],
        "knowsAbout": S["interests"], "url": absu("/"), "image": absu("/img/can-tian.jpg"),
    }
    same = [l["url"] for l in C["profile_links"] if l.get("url", "").startswith("http")]
    if same: person_ld["sameAs"] = same
    head = f'<script type="application/ld+json">{json.dumps(person_ld, ensure_ascii=False)}</script>'
    return page("/", S["name"], body, S["description"], head)


def research():
    wip = "".join(f"<li>{e(w['title'])}{(' <span class=\"muted\">(' + coauthors(w) + ')</span>') if coauthors(w) else ''}</li>"
                  for w in C.get("in_progress", []))
    body = f"""<h1>Research</h1>
<p class="muted">{e(', '.join(S['interests']).capitalize())}.</p>
<h2>Working papers</h2>
{''.join(paper_item(p) for p in WORKING)}
<h2>Publications</h2>
{''.join(paper_item(p) for p in PUBLISHED)}
<h2>Work in progress</h2>
<ul class="plain">{wip}</ul>"""
    return page("/research/", "Research", body, f"Research by {S['name']}: working papers, publications, and work in progress.")


def teaching():
    parts = []
    for inst in C["teaching"]:
        items = []
        for c in inst["courses"]:
            link = ""
            for l in c.get("links", []):
                href = l["url"] if ("://" in l["url"] or l["url"].startswith("/")) else f"/files/{l['url']}"
                link += f' · <a href="{e(href)}">{e(l["label"])}</a>'
            items.append(f"<li>{('<strong>' + e(c['code']) + '</strong> ') if c.get('code') else ''}{e(c['title'])} <span class='muted'>({e(c['level'])}) · {e(c['terms'])}</span>{link}</li>")
        parts.append(f"<h2>{e(inst['institution'])}</h2><ul class='plain'>{''.join(items)}</ul>")
    return page("/teaching/", "Teaching", "<h1>Teaching</h1>" + "".join(parts),
                f"Courses taught by {S['name']} at UNC Chapel Hill, Washington State University, and SUFE.")


def course_pages():
    out = {}
    for c in C.get("course_pages", []):
        items = "".join(f'<li><a href="/files/{e(c["files_dir"])}/{e(d["file"])}">{e(d["n"])}. {e(d["title"])}</a> <span class="muted small">({e(d["pages"])} pp.)</span></li>'
                        for d in c["decks"])
        body = f"""<p class="small"><a href="/teaching/">← Teaching</a></p>
<h1>{e(c['code'])}: {e(c['title'])}</h1>
<div class="title">{e(c['subtitle'])}</div>
{c['intro_html']}
<h2>Concept map</h2>
<p><a href="{e(c['map'])}">Open the interactive concept map →</a><br><span class="muted small">How the topics connect; each concept links to the handout pages where it is taught.</span></p>
<h2>Lecture handouts</h2>
<ul class="plain">{items}</ul>"""
        out[c["path"]] = page(c["path"], f"{c['code']} {c['term']}", body, c["description"])
    return out


def cv():
    cvd = C["cv"]
    rows = lambda xs: "".join(f"<dt>{e(a)}</dt><dd>{b}</dd>" for a, b in xs)
    body = f"""<h1>Curriculum vitae</h1>
<p><a href="/files/cv.pdf">Full CV (PDF)</a> <span class="muted small">· last updated {e(cvd['pdf_updated'])}</span></p>
<h2>Employment</h2><dl class="cv">{rows(cvd['employment'])}</dl>
<h2>Education</h2><dl class="cv">{rows(cvd['education'])}</dl>
<h2>Research</h2><p>{len(PUBLISHED)} publications and {len(WORKING)} working papers, listed on the <a href="/research/">research page</a>.</p>
<h2>Awards</h2><dl class="cv">{rows(cvd['awards'])}</dl>
<h2>Service</h2><dl class="cv">{rows(cvd['service'])}</dl>
<h2>Refereeing</h2><p>{e(cvd['referee'])}</p>"""
    return page("/cv/", "CV", body, f"Curriculum vitae of {S['name']}, {S['position']} at {S['institution']}.")


def life():
    L = C["life"]
    figs = "".join(
        f'<a href="/img/art/{a["file"]}.jpg"><img src="/img/art/{a["file"]}-sm.jpg" width="640" height="480" loading="lazy" alt="{e(a["alt"])}"></a>'
        for a in L["pieces"])
    projects = "".join(
        f'<article class="project"><h3><a href="{e(x["url"])}">{e(x["name"])}</a></h3>'
        f'<p>{e(x["blurb"])}</p>'
        f'<a href="{e(x["url"])}"><img src="/img/{e(x["image"])}" width="1200" height="900" loading="lazy" alt="{e(x["alt"])}"></a></article>'
        for x in L.get("projects", []))
    body = f"""<h1>Life</h1>
{L['intro_html']}
<h2>Things I make</h2>
{L.get('makes_html', '')}
<details class="drawings"><summary>{e(L['gallery_label'])}</summary>
<div class="gallery">{figs}</div>
</details>
{projects}"""
    return page("/life/", "Life", body, f"{S['name']} outside of economics: family, drawings by a self-taught amateur artist, and things she makes, like Podium, an iPad app for presenting Beamer slides.")


def zh():
    z = C["zh"]
    body = f"""<h1>{e(S['name_zh'])} <span class="muted">{e(S['name'])}</span></h1>
<div class="title muted">{e(z['title'])}</div>
{z['body_html']}
<p class="small"><a href="/">English homepage →</a></p>"""
    return page("/zh/", "中文简介", body, z["description"], lang="zh-CN")


def notfound():
    return page("/404.html", "Not found", '<h1>Page not found</h1><p>Try the <a href="/">home page</a> or <a href="/research/">research</a>.</p>', "Page not found")


# ---------- machine-readable files ----------
def llms_txt():
    L = [f"# {S['name']} ({S['name_zh']})", "",
         f"> {S['position']}, {S['department']}, {S['institution']}. {S['description']}", "",
         f"Email: {S['email']} (also {S['email_alt']})",
         f"Research interests: {', '.join(S['interests'])}.", "",
         "## Pages", ""]
    for u, t in NAV:
        L.append(f"- [{t}]({absu(u)})")
    L.append(f"- [CV (PDF)]({absu('/files/cv.pdf')})")
    for c in C.get("course_pages", []):
        L.append(f"- [{c['code']} {c['term']}: {c['title']}]({absu(c['path'])}): {c['description']}")
    for title, group in (("Working papers", WORKING), ("Publications", PUBLISHED)):
        L += ["", f"## {title}", ""]
        for p in group:
            venue = html.unescape(venue_line(p)).replace("<em>", "").replace("</em>", "")
            L.append(f"- [{p['title']}]({absu('/papers/' + p['slug'] + '/')}): {', '.join(p['authors'])}. {venue}."
                     + (f" DOI: {p['doi']}." if p.get("doi") else ""))
            if p.get("question"):
                L.append(f"  Question: {p['question']}")
            if p.get("abstract"):
                L.append(f"  Abstract: {p['abstract']}")
    L += ["", "## Work in progress", ""] + [f"- {w['title']}" + (f" ({', '.join(a for a in w['authors'] if a != S['name'])})" if len(w['authors']) > 1 else "") for w in C.get("in_progress", [])]
    if C["life"].get("projects"):
        L += ["", "## Software", ""] + [f"- [{x['name']}]({x['url']}): {x['blurb']}" for x in C["life"]["projects"]]
    prof = [f"- [{l['label']}]({l['url']})" for l in C["profile_links"] if l.get("url", "").startswith("http")]
    if prof: L += ["", "## Profiles", ""] + prof
    return "\n".join(L) + "\n"


def sitemap(paths):
    if not BASE:
        return None
    urls = "".join(f"<url><loc>{absu(p)}</loc><lastmod>{TODAY}</lastmod></url>" for p in paths)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n'


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#1d1b18"/><text x="32" y="43" font-family="Georgia,serif" font-size="30" font-weight="700" text-anchor="middle" fill="#faf7f1">CT</text></svg>"""


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    pages = {"/": home(), "/research/": research(), "/teaching/": teaching(), "/cv/": cv(),
             "/life/": life(), "/zh/": zh()}
    for p in PAPERS:
        pages[f"/papers/{p['slug']}/"] = paper_page(p)
    pages.update(course_pages())
    for path, text in pages.items():
        write(path + "index.html", text)
    write("/404.html", notfound())
    write("/favicon.svg", FAVICON)
    write("/llms.txt", llms_txt())
    sm = sitemap(pages)
    if sm:
        write("/sitemap.xml", sm)
    write("/robots.txt", "User-agent: *\nAllow: /\n" + (f"Sitemap: {absu('/sitemap.xml')}\n" if BASE else ""))
    write("/.nojekyll", "")
    if S.get("domain"):
        write("/CNAME", S["domain"])  # same bytes as the CNAME GitHub created
    print(f"Built {len(pages)} pages into {OUT}" + ("" if BASE else "  (base_url not set yet: no sitemap/canonical)"))


if __name__ == "__main__":
    main()
