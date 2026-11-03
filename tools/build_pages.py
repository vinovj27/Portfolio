"""Builds index.html and the project detail pages from src/ fragments."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
"""

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&family=JetBrains+Mono:wght@400;500&display=swap">
"""

GITHUB = '<svg viewBox="0 0 16 16" aria-hidden="true" style="fill:currentColor;stroke:none"><path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 7.59c.4.07.55-.17.55-.38v-1.33c-2.23.48-2.7-1.07-2.7-1.07-.36-.92-.89-1.17-.89-1.17-.73-.5.06-.49.06-.49.8.06 1.23.83 1.23.83.71 1.23 1.88.87 2.34.67.07-.52.28-.87.5-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48v2.2c0 .21.15.46.55.38A8 8 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>'

PAGES = [
    ("experience", "tcs", "Experience", "Software Engineering Intern · TCS"),
    ("projects", "conveyor", "Project", "Conveyor"),
    ("projects", "sift", "Project", "Sift"),
    ("projects", "kvlite", "Project", "KVLite"),
    ("projects", "petrem", "Project", "PetRem"),
]


def nav() -> str:
    return """  <header class="nav">
    <a class="brand" href="../index.html">Vinodhini Vijayakumar<span>.</span></a>
    <nav aria-label="Sections">
      <ul>
        <li class="opt"><a href="../index.html#experience">Experience</a></li>
        <li><a href="../index.html#projects">Projects</a></li>
        <li><a href="../index.html#contact" class="hire">Hire me</a></li>
      </ul>
    </nav>
  </header>
"""


def pager(folder: str, current: str) -> str:
    links = [f'<a href="{"" if f == folder else "../" + f + "/"}{slug}.html"><span>{label}</span><b>{name}</b></a>'
             for f, slug, label, name in PAGES if slug != current]
    return f"""    <section class="lean-block">
      <h2 class="mini">Keep exploring</h2>
      <div class="pager">{''.join(links)}</div>
    </section>
"""


def detail(folder: str, slug: str, title: str, description: str, hero: str, body: str, scripts: str = "") -> str:
    return (HEAD + f"<title>{title} · Vinodhini Vijayakumar</title>\n"
            '<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">\n'
            f'<meta name="description" content="{description}">\n'
            f'<meta property="og:title" content="{title} · Vinodhini Vijayakumar">\n'
            f'<meta property="og:description" content="{description}">\n'
            f'<meta property="og:url" content="https://vinovj27.github.io/Portfolio/{folder}/{slug}.html">\n'
            f'<meta property="og:image" content="https://vinovj27.github.io/Portfolio/assets/thumbs/{slug}.jpg">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            + FONTS + '<link rel="stylesheet" href="../assets/site.css">\n</head>\n<body>\n<div class="wrap">\n'
            + nav() + "  <main>\n" + hero + body + pager(folder, slug) + "  </main>\n"
            + """  <footer>
    <span>© 2026 Vinodhini</span>
    <a class="back" href="../index.html">← Back to portfolio</a>
  </footer>
</div>
""" + scripts + "</body>\n</html>\n")


def bust(html: str) -> str:
    import hashlib
    v = hashlib.sha256((ROOT / "assets" / "site.css").read_bytes()).hexdigest()[:8]
    return html.replace('href="assets/site.css"', f'href="assets/site.css?v={v}"').replace(
        'href="../assets/site.css"', f'href="../assets/site.css?v={v}"')


def build() -> None:
    page = (SRC / "page.html").read_text()
    head, body = page.split('<link rel="stylesheet" href="assets/site.css">', 1)
    (ROOT / "index.html").write_text(bust(HEAD + head.strip() + '\n<link rel="stylesheet" href="assets/site.css">\n</head>\n<body>\n'
                                     + body.strip() + "\n</body>\n</html>\n"))
    for folder, slug, _, _ in PAGES:
        out = ROOT / folder
        out.mkdir(exist_ok=True)
        frag = (SRC / folder / f"{slug}.html").read_text()
        meta, hero, content = frag.split("<!--SPLIT-->")
        lines = dict(line.split(": ", 1) for line in meta.strip().splitlines())
        html = detail(folder, slug, lines["title"], lines["description"], hero.replace("{GITHUB}", GITHUB), content)
        (out / f"{slug}.html").write_text(bust(html))
        print("built", out / f"{slug}.html")


if __name__ == "__main__":
    build()
