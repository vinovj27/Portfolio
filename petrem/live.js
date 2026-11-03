(() => {
  'use strict';
  const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/';
  const SESSION_KEY = 'petrem-live-session';
  window.PETREM_STATIC = true;

  const realFetch = window.fetch.bind(window);
  const pad = n => String(n).padStart(2, '0');
  const localNow = () => {
    const d = new Date();
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  };
  const status = text => { const el = document.querySelector('.boot span.msg'); if (el) el.textContent = text; };
  const store = {
    get() { try { return localStorage.getItem(SESSION_KEY); } catch { return null; } },
    set(v) { try { v ? localStorage.setItem(SESSION_KEY, v) : localStorage.removeItem(SESSION_KEY); } catch { /* private mode */ } },
  };

  let cookie = store.get();
  let py = null;
  let persistent = false;

  const sync = () => persistent ? new Promise(res => py.FS.syncfs(false, () => res())) : Promise.resolve();

  const ready = (async () => {
    status('Starting PetRem in your browser…');
    py = await loadPyodide({ indexURL: PYODIDE_URL });
    status('Loading the database engine…');
    try { await py.loadPackage(['sqlite3', 'hashlib']); } catch { await py.loadPackage('sqlite3'); }
    status('Loading PetRem…');
    const files = await (await realFetch('py/manifest.json')).json();
    py.FS.mkdirTree('/home/pyodide/petrem');
    await Promise.all(files.map(async name => {
      const res = await realFetch(`py/petrem/${name}`);
      if (!res.ok) throw new Error(`Couldn't load ${name} (${res.status})`);
      const src = await res.text();
      py.FS.writeFile(`/home/pyodide/petrem/${name}`, src);
    }));
    py.FS.mkdirTree('/data');
    try {
      py.FS.mount(py.FS.filesystems.IDBFS, {}, '/data');
      await new Promise((res, rej) => py.FS.syncfs(true, err => (err ? rej(err) : res())));
      persistent = true;
    } catch { persistent = false; }
    py.runPython(`
import sys
sys.path.insert(0, "/home/pyodide")
from petrem.browser import BrowserApp
petrem_app = BrowserApp("/data/petrem.db")
`);
    await sync();
    return py.globals.get('petrem_app');
  })();

  ready.catch(err => {
    console.error(err);
    status("Couldn't start the demo. Check your internet connection and reload the page.");
  });

  window.fetch = async (input, init = {}) => {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href);
    if (url.origin !== location.origin || !/^\/(api|calendar)\//.test(url.pathname)) return realFetch(input, init);
    const app = await ready;
    const method = (init.method || 'GET').toUpperCase();
    const headers = Object.fromEntries(new Headers(init.headers || {}).entries());
    if (cookie) headers.cookie = cookie;
    const out = JSON.parse(app.handle(method, url.pathname, JSON.stringify(headers), init.body || '', localNow()));
    if (out.cookie) {
      cookie = /Max-Age=0/.test(out.cookie) ? null : out.cookie.split(';')[0];
      store.set(cookie);
    }
    if (method !== 'GET') await sync();
    return new Response(out.body, { status: out.status, headers: { 'Content-Type': out.type } });
  };
})();
