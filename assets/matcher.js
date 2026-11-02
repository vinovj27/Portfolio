(() => {
  const EXPAND = { 'Ä': 'AE', 'Ö': 'OE', 'Ü': 'UE', 'ß': 'SS', 'Æ': 'AE', 'Œ': 'OE' };
  const DISTINCT = { 'Ł': 'L', 'Ø': 'O', 'Đ': 'D', 'Ħ': 'H', 'Ŧ': 'T', 'Þ': 'TH', 'Ð': 'D', 'ı': 'I' };
  const clean = s => s.toUpperCase().replace(/[-'’.,]/g, ' ').replace(/\s+/g, ' ').trim();
  const strip = s => s.normalize('NFD').replace(/\p{M}/gu, '');
  const distinct = s => s.replace(/[ŁØĐĦŦÞÐı]/g, c => DISTINCT[c] || c);
  const dedupe = s => [...new Set(s.split(' '))].join(' ');
  const plain = s => dedupe(strip(distinct(clean(s))));
  const expanded = s => dedupe(strip(distinct(clean(s).replace(/[ÄÖÜßÆŒ]/g, c => EXPAND[c]))));
  const first = s => s.split(' ')[0];
  const counts = s => { const m = {}; for (const ch of s.replace(/ /g, '')) m[ch] = (m[ch] || 0) + 1; return m; };
  const letterSim = (a, b) => {
    const ca = counts(a), cb = counts(b);
    let diff = 0;
    for (const k of new Set([...Object.keys(ca), ...Object.keys(cb)])) diff += Math.abs((ca[k] || 0) - (cb[k] || 0));
    const total = a.replace(/ /g, '').length + b.replace(/ /g, '').length;
    return total ? 1 - diff / total : 0;
  };
  const variants = s => [...new Set([plain(s), expanded(s)])];
  const anyEq = (xs, ys) => xs.some(x => ys.includes(x));

  function evaluate(af, al, bf, bl) {
    const steps = [];
    const done = v => ({ steps, verdict: v });
    const wordOne = s => first(dedupe(clean(s)));
    const normFirst = s => variants(s).map(first);

    const exact = clean(af) === clean(bf) && clean(al) === clean(bl);
    steps.push({ name: 'Exact match', ok: exact, detail: `${clean(af)} ${clean(al)}  vs  ${clean(bf)} ${clean(bl)}` });
    if (exact) return done({ kind: 'match', text: 'Matched at stage 1', conf: 100 });

    const fw = wordOne(af) === wordOne(bf) && wordOne(al) === wordOne(bl);
    steps.push({ name: 'First-word match', ok: fw, detail: `${wordOne(af)} ${wordOne(al)}  vs  ${wordOne(bf)} ${wordOne(bl)}  (repeated words removed)` });
    if (fw) return done({ kind: 'match', text: 'Matched at stage 2', conf: 100 });

    const accent = anyEq(normFirst(af), normFirst(bf)) && anyEq(normFirst(al), normFirst(bl));
    steps.push({ name: 'Accent-normalised match', ok: accent, detail: `${variants(af).join(' / ')} ${variants(al).join(' / ')}  vs  ${variants(bf).join(' / ')} ${variants(bl).join(' / ')}` });
    if (accent) return done({ kind: 'match', text: 'Matched at stage 3', conf: 100 });

    const pa = [plain(af), plain(al)], pb = [plain(bf), plain(bl)];
    const lenOk = Math.abs(pa[0].length - pb[0].length) <= 3 && Math.abs(pa[1].length - pb[1].length) <= 3;
    const sf = letterSim(pa[0], pb[0]), sl = letterSim(pa[1], pb[1]);
    const score = Math.min(sf, sl);
    const blob = Math.round(letterSim(pa.join(''), pb.join('')) * 100);
    const ok = lenOk && score >= 0.8;
    const detail = (lenOk ? `first names ${Math.round(sf * 100)}% · last names ${Math.round(sl * 100)}% · needs 80% on both` : 'length pre-filter rejects this pair before scoring')
      + ` · old combined-name method would have scored ${blob}%`;
    steps.push({ name: 'Possible match (letter frequency)', ok, detail });
    return done(ok
      ? { kind: 'review', text: 'Possible match: sent for human review', conf: Math.round(score * 100) }
      : { kind: 'none', text: 'No match: reported side by side for investigation', conf: null });
  }

  const STAGES = ['Exact match', 'First-word match', 'Accent-normalised match', 'Possible match (letter frequency)'];
  function withSkips(steps) {
    return STAGES.map(n => steps.find(s => s.name === n) || { name: n, skip: true, detail: 'skipped: already resolved' });
  }

  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  function render() {
    const vals = ['aFirst', 'aLast', 'bFirst', 'bLast'].map(id => $(id).value);
    if (vals.some(v => !v.trim())) {
      $('trace').innerHTML = '';
      $('verdict').innerHTML = '<span class="pill none">Enter all four names</span>';
      return;
    }
    const { steps, verdict } = evaluate(...vals);
    $('trace').innerHTML = withSkips(steps).map(s => `<div class="${s.skip ? 'skip' : s.ok ? 'hit' : 'miss'}"><span class="mark">${s.skip ? '–' : s.ok ? '✓' : '✗'}</span><span><strong>${esc(s.name)}</strong><br><code>${esc(s.detail)}</code></span></div>`).join('');
    const label = verdict.kind === 'match' ? 'MATCH' : verdict.kind === 'review' ? 'REVIEW' : 'NO MATCH';
    $('verdict').innerHTML = `<span class="pill ${verdict.kind}">${label}${verdict.conf != null ? ' · ' + verdict.conf + '%' : ''}</span><span>${esc(verdict.text)}</span>`;
  }
  ['aFirst', 'aLast', 'bFirst', 'bLast'].forEach(id => $(id).addEventListener('input', render));
  $('presets').querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
    const [af, al] = b.dataset.a.split('|'), [bf, bl] = b.dataset.b.split('|');
    $('aFirst').value = af; $('aLast').value = al; $('bFirst').value = bf; $('bLast').value = bl;
    render();
  }));
  render();
})();
