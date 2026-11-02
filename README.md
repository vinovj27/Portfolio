# vinodhini.dev

Personal portfolio of Vinodhini — software engineer building backend and data systems in Python.

**Live site:** https://vinovj27.github.io/Portfolio/

Hand-written HTML and CSS with no framework: a dark home page with clickable experience and project cards, each opening its own detail page, and a responsive layout down to phone width.

## Featured projects

| Project | What it is | Stack |
|---|---|---|
| [Conveyor](https://github.com/vinovj27/conveyor) | Distributed task queue with leases, retries and a dead-letter queue | Python |
| [Sift](https://github.com/vinovj27/sift) | Full-text search engine with BM25 ranking and instant-search UI | Python |
| [KVLite](https://github.com/vinovj27/kvlite) | Crash-safe key-value database with a TCP server | Python |

## Run locally

Open `index.html` in a browser, or serve the folder:

```bash
python -m http.server 8000
```

## Publish with GitHub Pages

To publish, open **Settings → Pages**, choose **Deploy from a branch**, branch `main`, folder `/ (root)`.

## Editing

- Home page content lives in `src/page.html`; detail pages live in `src/projects/` and `src/experience/`.
- Shared styles are in `assets/site.css`; card preview images are in `assets/thumbs/`.
- Project and experience pages are generated from the table in `tools/detail_pages.py`: edit it, then run `python tools/detail_pages.py && python tools/build_pages.py`.
- After editing `src/page.html`, run `python tools/build_pages.py` to regenerate `index.html`, `projects/` and `experience/`.
- Replace `assets/vinodhini-round.jpg` to change the photo (square crop, about 720 px).
