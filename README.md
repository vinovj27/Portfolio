# vinodhini.dev

Personal portfolio of Vinodhini — software engineer building backend and data systems in Python.

**Live site:** https://vinovj27.github.io/Portfolio/

A single hand-written HTML page: no build step, no framework, light and dark themes, and a responsive layout down to phone width.

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

- Text and links live in `index.html`; `src/page.html` is the same page without the document wrapper.
- Colors and fonts are tokens at the top of the `<style>` block.
- Replace `assets/vinodhini.jpg` to change the photo (portrait crop, about 720 px wide).
