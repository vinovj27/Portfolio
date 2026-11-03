"""Generates the detail-page fragments in src/projects and src/experience from the PAGES table."""
from pathlib import Path
ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M9 7h8v8"/></svg>'
ICONS = {
 "bolt": '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>',
 "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3z"/><path d="m9 12 2 2 4-4"/>',
 "refresh": '<path d="M20 11a8 8 0 0 0-14.9-3M4 4v4h4M4 13a8 8 0 0 0 14.9 3M20 20v-4h-4"/>',
 "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
 "text": '<path d="M4 7V5h16v2M9 19h6M12 5v14"/>',
 "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"/>',
 "disk": '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
 "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
 "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20a6.5 6.5 0 0 0-4-6"/>',
 "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
 "file": '<path d="M14 3H6v18h12V7l-4-4z"/><path d="M14 3v4h4M9 13h6M9 17h6"/>',
 "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
}
def icon(n): return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[n]}</svg>'

PAGES = {
 ("projects","conveyor"): dict(
   title="Conveyor", desc="Conveyor, a distributed task queue in Python with leases, retries and a dead-letter queue. Built by Vinodhini.",
   back="../index.html#projects", eyebrow="Distributed systems · Python", h1="Conveyor",
   tagline="A task queue that keeps working when workers crash.",
   buttons=[("View project","https://github.com/vinovj27/Conveyor",True),("Source code","https://github.com/vinovj27/Conveyor/tree/main/conveyor",False)],
   shot=("../assets/thumbs/conveyor.jpg","Conveyor's live dashboard after a demo run"),
   figs=[("0","jobs lost when a worker is killed"),("0","duplicate claims under 8-thread races"),("151","jobs in ~6 s across 3 processes")],
   hl=[("shield","Crash-proof","Leases expire on dead workers, so their jobs go to healthy ones."),
       ("refresh","Smart retries","Exponential backoff with jitter, then a dead-letter queue."),
       ("chart","Live dashboard","Queue depth, workers and one-click retry, updated every second.")],
   stack=["Python","SQLite","HTTP API","Multiprocessing","GitHub Actions"]),
 ("projects","sift"): dict(
   title="Sift", desc="Sift, a full-text search engine in Python with BM25 ranking, phrase queries and typo correction. Built by Vinodhini.",
   back="../index.html#projects", eyebrow="Search engine · Python", h1="Sift",
   tagline="A search engine that answers in milliseconds and forgives typos.",
   buttons=[("View project","https://github.com/vinovj27/Sift",True),("Source code","https://github.com/vinovj27/Sift/tree/main/sift",False)],
   shot=("../assets/thumbs/sift.jpg","Sift returning ranked, highlighted results"),
   figs=[("1–5 ms","typical query time"),("3,930","documents indexed"),("0","external dependencies")],
   hl=[("bolt","BM25 ranking","The same scoring model behind Elasticsearch and Lucene."),
       ("search","Smart queries","\"Exact phrases\", +required and -excluded words."),
       ("spark","Did you mean?","Typo correction, autocomplete and highlighted snippets.")],
   stack=["Python","Algorithms","Information retrieval","JSON API","JavaScript"]),
 ("projects","kvlite"): dict(
   title="KVLite", desc="KVLite, a crash-safe key-value database in Python with a write-ahead log and TCP server. Built by Vinodhini.",
   back="../index.html#projects", eyebrow="Database · Python", h1="KVLite",
   tagline="A database that survives a pulled plug.",
   buttons=[("View project","https://github.com/vinovj27/Kvlite",True),("Source code","https://github.com/vinovj27/Kvlite/tree/main/kvlite",False)],
   shot=("../assets/thumbs/kvlite.jpg","KVLite recovering every record after a restart"),
   figs=[("~59K","writes per second"),("~1.6M","reads per second"),("0","writes lost across restarts")],
   hl=[("disk","Write-ahead log","Every write is logged before it's applied."),
       ("lock","Crash recovery","Checksums catch half-written records and roll back cleanly."),
       ("users","Many clients","A TCP server with a Redis-style protocol.")],
   stack=["Python","Write-ahead log","CRC32","TCP sockets","GitHub Actions"]),
 ("projects","petrem"): dict(
   title="PetRem", desc="PetRem, a full-stack pet vaccination and care reminder app: Python REST API, SQLite and a single-page frontend. Built by Vinodhini.",
   back="../index.html#projects", eyebrow="Full-stack web app · Python + JavaScript", h1="PetRem",
   tagline="Never miss a pet's vaccine. Plans, reminders and calendar sync in one app.",
   buttons=[("Live demo","../petrem/",True),("View project","https://github.com/vinovj27/Petrem-app",False),("Source code","https://github.com/vinovj27/Petrem-app/tree/main/petrem",False)],
   shot=("../assets/thumbs/petrem.jpg","PetRem's Today dashboard with overdue vaccines and upcoming reminders"),
   figs=[("37","automated tests, CI on 3 operating systems"),("23","REST API endpoints"),("0","external dependencies")],
   hl=[("lock","Secure accounts","Hashed passwords, HttpOnly sessions, rate-limited logins and per-user data isolation."),
       ("spark","Smart vaccine plans","Due dates calculated from each pet's species, age and dose history."),
       ("chart","Reminders & calendar","Repeating reminders, desktop alerts and a live feed for Google or Apple Calendar.")],
   stack=["Python","REST API","SQLite","JavaScript","HTML & CSS","Authentication"]),
 ("experience","tcs"): dict(
   title="Software Engineering Intern, TCS", desc="Vinodhini's software engineering internship at Tata Consultancy Services, May–Aug 2026.",
   back="../index.html#experience", eyebrow="Work experience · May – Aug 2026", h1="Software Engineering Intern",
   tagline="Tata Consultancy Services · Python data reconciliation for a bank's platform migration.",
   buttons=[],
   shot=("../assets/thumbs/tcs.jpg","Illustration of name records matched across systems with confidence scores"),
   figs=[("85K+","signer records reconciled"),("4","banking systems compared"),("3","analyses delivered")],
   hl=[("globe","International names","Matched names across umlauts, accents and spelling conventions."),
       ("bolt","Built to scale","Kept the tool fast as data more than doubled mid-project."),
       ("file","Reviewer-ready reports","Excel reports with a confidence score on every match.")],
   stack=["Python","Data reconciliation","Fuzzy matching","Unicode","Excel"]),
}

def fragment(p):
    btns = "".join(f'<a class="btn{" primary" if prim else ""}" href="{u}" target="_blank" rel="noopener">{"" if prim else "{GITHUB}"}{t}{ARROW if prim else ""}</a>' for t,u,prim in p["buttons"])
    cta = f'\n      <div class="cta-row">{btns}</div>' if btns else ""
    hero = f'''
    <section class="d-hero lean">
      <a class="back" href="{p["back"]}">← Back to portfolio</a>
      <span class="eyebrow">{p["eyebrow"]}</span>
      <h1>{p["h1"]}</h1>
      <p class="tagline">{p["tagline"]}</p>{cta}
      <img class="d-shot" src="{p["shot"][0]}" alt="{p["shot"][1]}" width="960" height="600">
    </section>
'''
    figs = "".join(f'<div><b>{n}</b><span>{l}</span></div>' for n,l in p["figs"])
    hl = "".join(f'<article><span class="ic">{icon(i)}</span><h3>{t}</h3><p>{d}</p></article>' for i,t,d in p["hl"])
    chips = "".join(f'<span class="chip{" hot" if k==0 else ""}">{c}</span>' for k,c in enumerate(p["stack"]))
    body = f'''
    <section class="lean-block"><div class="big-figs">{figs}</div></section>
    <section class="lean-block"><h2 class="mini">Highlights</h2><div class="hl-cards">{hl}</div></section>
    <section class="lean-block"><h2 class="mini">Built with</h2><div class="chips">{chips}</div></section>
'''
    return f'title: {p["title"]}\ndescription: {p["desc"]}\n<!--SPLIT-->{hero}<!--SPLIT-->{body}'

for (folder, slug), p in PAGES.items():
    Path(f"src/{folder}/{slug}.html").write_text(fragment(p))
    print("wrote", folder, slug)
