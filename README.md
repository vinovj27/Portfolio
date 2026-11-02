# vinodhini.dev

Personal portfolio of Vinodhini — software engineer building backend and data systems in Python.

**Live site:** https://vinovj27.github.io/Portfolio/

A single hand-written HTML page: no build step, no framework, a dark design, an interactive name-matching demo from my TCS internship, and a responsive layout down to phone width.

## Featured projects

| Project | What it is | Stack |
|---|---|---|
| [Conveyor](https://github.com/vinovj27/conveyor) | Distributed task queue with leases, retries and a dead-letter queue | Python |
| [Sift](https://github.com/vinovj27/sift) | Full-text search engine with BM25 ranking and instant-search UI | Python |
| [KVLite](https://github.com/vinovj27/kvlite) | Crash-safe key-value database with an asyncio TCP server | Python |

## Run locally

Open `index.html` in a browser, or serve the folder:

```bash
python -m http.server 8000
```

## Publish with GitHub Pages

To publish, open **Settings → Pages**, choose **Deploy from a branch**, branch `main`, folder `/ (root)`.

## Editing

- Home page content lives in `src/page.html`; detail pages live in `src/projects/`.
- Shared styles are in `assets/site.css`; the TCS name-matching demo is `assets/matcher.js`.
- After editing anything in `src/`, run `python tools/build_pages.py` to regenerate `index.html` and `projects/`.
- Replace `assets/vinodhini-round.jpg` to change the photo (square crop, about 720 px).
