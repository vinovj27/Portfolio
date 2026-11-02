# vinodhini.dev

Personal portfolio of Vinodhini — software engineer focused on banking and data systems.

**Live site:** https://vinovj27.github.io/portfolio/

A single hand-written HTML page: no build step, no framework, light and dark themes, and a responsive layout down to phone width.

## Featured projects

| Project | What it is | Stack |
|---|---|---|
| [LedgerFlow](https://github.com/vinovj27/ledgerflow) | Core-banking ledger with atomic, idempotent transfers | Java 17 |
| [KVLite](https://github.com/vinovj27/kvlite) | Crash-safe key-value database with a TCP server | Java 17 |
| [TxnGuard](https://github.com/vinovj27/txnguard) | Real-time explainable fraud detection | Python |

## Run locally

Open `index.html` in a browser, or serve the folder:

```bash
python -m http.server 8000
```

## Publish with GitHub Pages

1. Push this folder to a repository named `portfolio`.
2. In the repository, open **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, branch `main`, folder `/ (root)`.
4. The site appears at `https://vinovj27.github.io/portfolio/` within a minute or two.

To serve it from `https://vinovj27.github.io/` instead, name the repository `vinovj27.github.io`.

## Editing

- Text and links live in `index.html`; `src/page.html` is the same page without the document wrapper.
- Colors and fonts are tokens at the top of the `<style>` block.
- Replace `assets/vinodhini.jpg` to change the photo (portrait crop, about 720 px wide).
