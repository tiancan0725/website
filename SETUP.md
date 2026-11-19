# Going live: domain + GitHub (about 30 minutes, once)

You do the clicks that involve accounts and payment; Claude does everything in this folder.

## 1. Pick and buy a domain (~$10–15/year)

Ideas: `cantian.org`, `cantian.net`, `cantianecon.com`, `tiancan.com` (first one available wins; `.org`/`.com`/`.net` all fine).

Registrar: **Porkbun** (porkbun.com): plain pricing, free WHOIS privacy, no upsells you need.
(Cloudflare Registrar is equally good and at cost, but needs a few more setup steps.)

- Search the name, add to cart, check the **renewal** price (not just year one).
- Skip every add-on (email, hosting, SSL: GitHub gives you SSL free).
- Turn on **auto-renew** so it never lapses (a lapsed academic domain gets bought by spammers).

## 2. GitHub account and the repository

1. Sign up at github.com (free). The username barely matters once you have your own domain.
2. Install **GitHub Desktop** (desktop.github.com) and sign in.
3. In GitHub Desktop: *File → Add Local Repository…* → choose this folder (`Dropbox/Public/personal web`). It will say the folder isn't a Git repository yet: click **create a repository** (keep the defaults, *Git ignore: None*; the folder already has its own `.gitignore`), then **Create Repository**.
4. Click **Publish repository**. Name it `website`; **untick** "Keep this code private" (free GitHub Pages needs a public repository; everything in it is public website material anyway).

## 3. Turn on GitHub Pages

On github.com, open the repository → **Settings → Pages**:
- *Source*: Deploy from a branch → `main` → `/docs` → **Save**.
- *Custom domain*: type your domain (e.g. `cantian.org`) → **Save**.

## 4. Point the domain at GitHub (at Porkbun → your domain → DNS)

Delete Porkbun's default "parked" records, then add:

| Type  | Host  | Answer                    |
|-------|-------|---------------------------|
| A     | (blank) | 185.199.108.153         |
| A     | (blank) | 185.199.109.153         |
| A     | (blank) | 185.199.110.153         |
| A     | (blank) | 185.199.111.153         |
| CNAME | www   | YOUR-GITHUB-USERNAME.github.io |

(These are GitHub's published addresses; see docs.github.com → "Managing a custom domain for your GitHub Pages site".)

Within minutes to a few hours, the Pages settings page shows the DNS check passing. Then tick **Enforce HTTPS**.

Recommended extra (stops anyone else from hijacking the domain on GitHub): github.com → your profile **Settings → Pages → Add a domain**, and add the TXT record it shows you at Porkbun.

## 5. Tell Claude the domain

Claude sets it in `content.toml`, rebuilds (sitemap, canonical links, CNAME), and commits. You click **Push origin** in GitHub Desktop. Done.

## 6. Be found (after it's live)

- **Google Search Console** (search.google.com/search-console): add the domain, verify via a TXT record at Porkbun, submit `sitemap.xml`.
- **Bing Webmaster Tools**: import from Google Search Console in one click (Bing also feeds DuckDuckGo and several AI assistants).
- Put the new URL on: Google Scholar profile, RePEc/IDEAS, ORCID, NBER profile, UNC directory page, email signature, and the CV (the CV still says tiancan.weebly.com).
- **Weebly**: replace the home page with one line, "This site has moved to <new address>", keep it a few months, then cancel.

## Updating later

Tell Claude what changed ("JPE accepted!", "new draft of the knowledge paper", "add this drawing"). Claude edits `content.toml`, rebuilds, commits; you click **Push** in GitHub Desktop. The live site updates in about a minute.
