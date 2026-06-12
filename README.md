# Family Timeline — web view

A single-file, self-contained web page presenting the Hutcheson / Chancey / Mixon
family timeline, with every entry color-coded by how solid the evidence is
(confidence rating), plus search and filters by era, family, and confidence.

`timeline_v9.md` is the **canonical source**. `index.html` is **generated** from it
— do not hand-edit `index.html` for content; edit the Markdown and rebuild.

## Files
- `index.html` — the **research view** (data embedded inline; **opens by double-click, no server needed**)
- `index-public.html` — the **public view** (same data, but internal source citations and audit-only entries are omitted; share this one)
- `timeline_v9.md` — the canonical timeline (copy of the research project's file)
- `build.py` — regenerates **both** pages from `timeline_v9.md`
- `.nojekyll` — tells GitHub Pages to serve the files as-is

## Two views from one source
Both pages are generated from the same `timeline_v9.md` — there is no second
content file to keep in sync. One `python3 build.py` writes both:
- **`index.html` (research view)** — everything: internal `source_*.md` / D- / Q-
  citations and audit-only rows (REFUTED claims, same-name-disambiguation notes).
- **`index-public.html` (public view)** — for readers who aren't the researcher:
  the source/citation line is hidden and **research-only rows are dropped**.
  A row counts as research-only if its confidence is REFUTED or purely 🔴, **or**
  if you add the tag **`[research-only]`** anywhere in its event text in the
  Markdown (the tag itself is stripped from display). Use that tag to hide any
  additional internal-only entry from the public view without deleting it.

(Still a known limitation: inline project shorthand like "(D-11, resolved-on-weight)"
inside otherwise-public sentences is *not* yet stripped — that's a planned next step.)

## View it locally
Just **double-click `index.html`** — it works offline, no web server required.

## Update it
1. Replace `timeline_v9.md` with the latest version from the research project.
2. Run: `python3 build.py`
3. Commit and push the regenerated `index.html`.

## Host it on GitHub Pages (free)
1. On GitHub, create a **new repository** (e.g., `family-timeline`).
2. Push this folder to it (via the GitHub Desktop app: add this folder as a repo, publish it).
3. In the repo on github.com: **Settings → Pages → Build and deployment → Source: "Deploy from a branch" → Branch: `main` / `/ (root)` → Save.**
4. Wait ~1 minute. The site appears at:
   `https://<your-username>.github.io/family-timeline/`
5. Share that URL with your small group.

### Privacy — important
On a free GitHub account, **a Pages site is publicly viewable even if the repo is private.**
Truly access-controlled Pages requires a paid GitHub Enterprise plan. This page
includes a `noindex` tag (search engines are asked to skip it) and the URL is
obscure, so it's effectively "unlisted" — fine for low-sensitivity, historical
data, but **anyone with the link can view it.** This timeline is all historical
(ends ~1904, no living people), so that's an acceptable bar. **Do not add
living-people data** (e.g., the descent index) to this page without reconsidering.
For truly private sharing instead, email `index.html` directly (it's one file).
