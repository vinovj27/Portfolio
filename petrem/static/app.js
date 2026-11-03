(() => {
  'use strict';

  const ICONS = {
    home: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    paw: '<circle cx="5.5" cy="10" r="2"/><circle cx="9.5" cy="5.5" r="2"/><circle cx="14.5" cy="5.5" r="2"/><circle cx="18.5" cy="10" r="2"/><path d="M12 11c-3 0-6 4.5-6 7a3 3 0 0 0 3 3c1.2 0 2-.6 3-.6s1.8.6 3 .6a3 3 0 0 0 3-3c0-2.5-3-7-6-7z"/>',
    cat: '<path d="M5 3.5 9 8h6l4-4.5V13a7 7 0 0 1-14 0z"/><path d="M9.5 13h.01M14.5 13h.01M10.5 16.5 12 17.5l1.5-1"/>',
    heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    bell: '<path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    list: '<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6h.01M4 12h.01M4 18h.01"/>',
    syringe: '<path d="m18 2 4 4M16 4l4 4M14.5 5.5l4 4-9 9H5.5v-4z"/><path d="m11 9 2 2M8.5 11.5l2 2M2 22l3.5-3.5"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6"/><path d="M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    logout: '<path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10"/>',
    back: '<path d="M15 6l-6 6 6 6"/>',
    repeat: '<path d="M17 2l3 3-3 3"/><path d="M4 11V9a4 4 0 0 1 4-4h12M7 22l-3-3 3-3"/><path d="M20 13v2a4 4 0 0 1-4 4H4"/>',
    shield: '<path d="M12 3 5 6v6c0 4.5 3 7.7 7 9 4-1.3 7-4.5 7-9V6z"/><path d="m9 12 2 2 4-4"/>',
    spark: '<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
  };
  const icon = (name, cls = 'i') => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name]}</svg>`;
  const SPECIES_ICON = { dog: 'paw', cat: 'cat', other: 'heart' };
  const SPECIES_LABEL = { dog: 'Dog', cat: 'Cat', other: 'Other pet' };
  const REPEAT_LABEL = { none: 'One time', daily: 'Every day', weekly: 'Every week', monthly: 'Every month', yearly: 'Every year' };
  const SUGGESTIONS = [
    ['Flea & tick treatment', 'monthly'], ['Heartworm pill', 'monthly'], ['Deworming tablet', 'monthly'],
    ['Grooming appointment', 'none'], ['Annual check-up', 'yearly'], ['Nail trim', 'monthly'], ['Refill food', 'none'],
  ];

  const state = { me: null, config: { demo: false }, vaccines: null, pets: null, reminders: new Map(), notes: { items: [], unread: 0 }, lastAlerted: 0, tab: 'upcoming' };
  const app = document.getElementById('app');
  const modalRoot = document.getElementById('modal-root');

  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pad = n => String(n).padStart(2, '0');
  const localISO = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const parseDate = iso => { const [y, m, d] = iso.split('-').map(Number); return new Date(y, m - 1, d); };
  const fmtDate = iso => {
    const d = parseDate(iso);
    const opts = { month: 'short', day: 'numeric' };
    if (d.getFullYear() !== new Date().getFullYear()) opts.year = 'numeric';
    return d.toLocaleDateString(undefined, opts);
  };
  const fmtTime = hm => { const [h, m] = hm.split(':').map(Number); return new Date(2000, 0, 1, h, m).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }); };
  const daysFrom = iso => Math.round((parseDate(iso) - parseDate(localISO(new Date()))) / 86400000);
  const relDay = days => days === 0 ? 'Today' : days === 1 ? 'Tomorrow' : days === -1 ? 'Yesterday'
    : days < 0 ? `${-days} days overdue` : days < 14 ? `In ${days} days` : null;
  const whenLabel = (iso, time) => {
    const days = daysFrom(iso);
    const base = relDay(days) || fmtDate(iso);
    return { text: time ? `${base} · ${fmtTime(time)}` : base, cls: days < 0 ? 'overdue' : days === 0 ? 'today' : '' };
  };
  const firstName = name => (name || '').trim().split(/\s+/)[0] || 'there';

  async function api(method, path, body) {
    const opts = { method, headers: { 'X-PetRem': '1' }, credentials: 'same-origin' };
    if (body !== undefined) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
    let res;
    try { res = await fetch(path, opts); } catch { throw new Error("Can't reach PetRem. Check that the server is running."); }
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      if (res.status === 401 && state.me && !path.endsWith('/login')) { state.me = null; route(); }
      const err = new Error(data?.error || `Request failed (${res.status})`);
      err.status = res.status;
      throw err;
    }
    return data;
  }

  function toast(message, kind = '') {
    const el = document.createElement('div');
    el.className = `toast ${kind}`;
    el.innerHTML = `${icon(kind === 'err' ? 'x' : 'check')}<span>${esc(message)}</span>`;
    document.getElementById('toasts').append(el);
    setTimeout(() => el.remove(), 3200);
  }

  // ---------- small components ----------

  const ava = (pet, cls = '') => `<span class="ava ${cls} c${pet.color % 8}" aria-hidden="true">${esc(pet.name[0]?.toUpperCase() || '?')}<span class="sp">${icon(SPECIES_ICON[pet.species])}</span></span>`;
  const chip = pet => `<a class="chip" href="#/pets/${pet.id}"><span class="mini c${pet.color % 8}">${esc(pet.name[0]?.toUpperCase())}</span>${esc(pet.name)}</a>`;
  const empty = (iconName, title, text, action = '') => `<div class="empty"><div class="big">${icon(iconName)}</div><h3>${esc(title)}</h3><p>${esc(text)}</p>${action}</div>`;
  const skeleton = n => `<div class="list">${'<div class="skeleton"></div>'.repeat(n)}</div>`;

  function vaxStatus(v) {
    if (v.status === 'overdue') return `Overdue since ${fmtDate(v.next_due)}`;
    const rel = relDay(v.days);
    if (v.status === 'due_soon') return `Due ${rel ? rel.toLowerCase() : fmtDate(v.next_due)}`;
    return `Next ${fmtDate(v.next_due)}`;
  }

  function agendaItem(i) {
    const when = whenLabel(i.due, i.time);
    const isVax = i.kind === 'vaccine';
    const title = isVax ? `<a class="title" href="#/pets/${i.pet.id}">${esc(i.title)}</a>` : `<span class="title">${esc(i.title)}</span>`;
    const repeat = i.repeat && i.repeat !== 'none' ? `<span class="tag">${REPEAT_LABEL[i.repeat]}</span>` : '';
    const action = isVax
      ? `<button class="btn sm" data-action="add-dose" data-pet="${i.pet.id}" data-species="${i.pet.species}" data-vaccine="${esc(i.vaccine)}">${icon('check')}Mark given</button>`
      : `<button class="btn sm primary" data-action="done-reminder" data-id="${i.id}">${icon('check')}Done</button>`;
    return `<div class="item ${when.cls === 'overdue' ? 'overdue' : ''}">
      <span class="kind ${isVax ? 'vaccine' : ''}">${icon(isVax ? 'syringe' : 'bell')}</span>
      <div class="main">${title}<div class="meta"><span class="when ${when.cls}">${when.text}</span>${i.pet ? chip(i.pet) : ''}${repeat}</div></div>
      <div class="acts">${action}</div>
    </div>`;
  }

  function reminderRow(r) {
    state.reminders.set(r.id, r);
    const [d, t] = r.due_at.split('T');
    const when = r.done_at ? { text: `Done ${fmtDate(r.done_at.split('T')[0])}`, cls: '' } : whenLabel(d, t);
    const repeat = r.repeat !== 'none' ? `<span class="tag">${REPEAT_LABEL[r.repeat]}</span>` : '';
    const acts = r.done_at
      ? `<button class="btn sm ghost" data-action="edit-reminder" data-id="${r.id}">${icon('repeat')}Reschedule</button>
         <button class="btn icon ghost danger" data-action="del-reminder" data-id="${r.id}" aria-label="Delete reminder">${icon('trash')}</button>`
      : `<button class="btn sm primary" data-action="done-reminder" data-id="${r.id}">${icon('check')}Done</button>
         <button class="btn icon ghost" data-action="edit-reminder" data-id="${r.id}" aria-label="Edit reminder">${icon('edit')}</button>
         <button class="btn icon ghost danger" data-action="del-reminder" data-id="${r.id}" aria-label="Delete reminder">${icon('trash')}</button>`;
    return `<div class="item ${when.cls === 'overdue' ? 'overdue' : ''}">
      <span class="kind">${icon(r.repeat !== 'none' ? 'repeat' : 'bell')}</span>
      <div class="main"><span class="title">${esc(r.title)}</span>
        <div class="meta"><span class="when ${when.cls}">${when.text}</span>${r.pet ? chip(r.pet) : ''}${repeat}</div>
        ${r.notes ? `<div class="meta">${esc(r.notes)}</div>` : ''}</div>
      <div class="acts">${acts}</div>
    </div>`;
  }

  // ---------- modals ----------

  function openModal({ title, body, submit = 'Save', danger = false, onSubmit }) {
    closeModal();
    const wrap = document.createElement('div');
    wrap.className = 'backdrop';
    wrap.innerHTML = `<form class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" novalidate>
      <div class="modal-head"><h2 id="modal-title">${esc(title)}</h2><button type="button" class="btn icon ghost" data-close aria-label="Close">${icon('x')}</button></div>
      <div class="modal-body stack"><div class="form-error" hidden></div>${body}</div>
      ${onSubmit ? `<div class="modal-foot"><button type="button" class="btn ghost" data-close>Cancel</button><button type="submit" class="btn ${danger ? 'danger solid' : 'primary'}">${esc(submit)}</button></div>` : ''}
    </form>`;
    const form = wrap.querySelector('form');
    wrap.addEventListener('mousedown', e => { if (e.target === wrap) closeModal(); });
    wrap.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', closeModal));
    form.addEventListener('submit', async e => {
      e.preventDefault();
      if (!onSubmit) return;
      const btn = form.querySelector('[type=submit]');
      const errBox = form.querySelector('.form-error');
      btn.disabled = true;
      errBox.hidden = true;
      try {
        await onSubmit(form);
        closeModal();
      } catch (err) {
        errBox.textContent = err.message;
        errBox.hidden = false;
        btn.disabled = false;
      }
    });
    modalRoot.append(wrap);
    (form.querySelector('input:not([type=hidden]), select, textarea') || form.querySelector('[type=submit]'))?.focus();
    return form;
  }
  function closeModal() { modalRoot.innerHTML = ''; }
  const val = (form, name) => form.elements[name]?.value ?? '';

  async function ensureVaccines() {
    if (!state.vaccines) state.vaccines = await api('GET', '/api/vaccines');
    return state.vaccines;
  }
  async function ensurePets(force = false) {
    if (!state.pets || force) state.pets = (await api('GET', '/api/pets')).pets;
    return state.pets;
  }

  function petForm(pet = null) {
    const today = localISO(new Date());
    openModal({
      title: pet ? `Edit ${pet.name}` : 'Add a pet',
      submit: pet ? 'Save changes' : 'Add pet',
      body: `
        <label class="field"><span>Name</span><input class="input" name="name" maxlength="60" required value="${esc(pet?.name)}" placeholder="e.g. Biscuit"></label>
        <div class="row2">
          <label class="field"><span>Species</span><select class="input" name="species">
            ${['dog', 'cat', 'other'].map(s => `<option value="${s}" ${pet?.species === s ? 'selected' : ''}>${SPECIES_LABEL[s]}</option>`).join('')}
          </select></label>
          <label class="field"><span>Breed</span><input class="input" name="breed" maxlength="60" value="${esc(pet?.breed)}" placeholder="Optional"></label>
        </div>
        <div class="row2">
          <label class="field"><span>Birth date</span><input class="input" type="date" name="birth_date" max="${today}" required value="${esc(pet?.birth_date)}"><small>An estimate is fine for rescues.</small></label>
          <label class="field"><span>Sex</span><select class="input" name="sex">
            <option value="">Not set</option><option value="female" ${pet?.sex === 'female' ? 'selected' : ''}>Female</option><option value="male" ${pet?.sex === 'male' ? 'selected' : ''}>Male</option>
          </select></label>
        </div>
        <label class="field"><span>Weight (kg)</span><input class="input" type="number" name="weight_kg" min="0.1" max="200" step="0.1" value="${pet?.weight_kg ?? ''}" placeholder="Optional"></label>
        <label class="field"><span>Notes</span><textarea class="input" name="notes" maxlength="1000" placeholder="Allergies, vet details, habits…">${esc(pet?.notes)}</textarea></label>
        ${pet ? '<p class="disclaimer">Changing species removes vaccine doses that don\'t apply to the new species.</p>' : ''}`,
      onSubmit: async form => {
        const data = { name: val(form, 'name'), species: val(form, 'species'), breed: val(form, 'breed'), birth_date: val(form, 'birth_date'), sex: val(form, 'sex'), weight_kg: val(form, 'weight_kg'), notes: val(form, 'notes') };
        const saved = pet ? await api('PUT', `/api/pets/${pet.id}`, data) : await api('POST', '/api/pets', data);
        state.pets = null;
        toast(pet ? `${saved.name} updated` : `${saved.name} added. Their vaccine plan is ready.`);
        if (!pet) location.hash = `#/pets/${saved.id}`; else route();
      },
    });
  }

  async function doseForm(petId, species, vaccineCode) {
    const all = (await ensureVaccines())[species] || [];
    const today = localISO(new Date());
    openModal({
      title: 'Record a vaccine dose',
      submit: 'Save dose',
      body: `
        <label class="field"><span>Vaccine</span><select class="input" name="vaccine">
          ${all.map(v => `<option value="${v.code}" ${v.code === vaccineCode ? 'selected' : ''}>${esc(v.name)} · ${esc(v.protects)}</option>`).join('')}
        </select></label>
        <label class="field"><span>Date given</span><input class="input" type="date" name="given_on" max="${today}" value="${today}" required></label>
        <label class="field"><span>Notes</span><input class="input" name="notes" maxlength="300" placeholder="Clinic, batch number… (optional)"></label>`,
      onSubmit: async form => {
        const pet = await api('POST', `/api/pets/${petId}/doses`, { vaccine: val(form, 'vaccine'), given_on: val(form, 'given_on'), notes: val(form, 'notes') });
        const v = pet.vaccines.find(x => x.code === val(form, 'vaccine'));
        toast(`Saved. Next ${v.name} due ${fmtDate(v.next_due)}`);
        state.pets = null;
        route();
      },
    });
  }

  async function reminderForm(reminder = null, presetPet = null) {
    const pets = await ensurePets();
    const now = new Date();
    now.setHours(now.getHours() + 1, 0, 0, 0);
    const [d, t] = reminder ? reminder.due_at.split('T') : [localISO(now), `${pad(now.getHours())}:00`];
    const petId = reminder?.pet?.id ?? presetPet;
    const form = openModal({
      title: reminder ? 'Edit reminder' : 'New reminder',
      submit: reminder ? 'Save reminder' : 'Add reminder',
      body: `
        <label class="field"><span>What needs doing?</span><input class="input" name="title" maxlength="100" required value="${esc(reminder?.title)}" placeholder="e.g. Flea & tick treatment"></label>
        ${reminder ? '' : `<div class="suggest">${SUGGESTIONS.map(([s, r]) => `<button type="button" data-title="${esc(s)}" data-repeat="${r}">${esc(s)}</button>`).join('')}</div>`}
        <label class="field"><span>For</span><select class="input" name="pet_id">
          <option value="">All pets / general</option>
          ${pets.map(p => `<option value="${p.id}" ${p.id === petId ? 'selected' : ''}>${esc(p.name)}</option>`).join('')}
        </select></label>
        <div class="row2">
          <label class="field"><span>Date</span><input class="input" type="date" name="date" value="${d}" required></label>
          <label class="field"><span>Time</span><input class="input" type="time" name="time" value="${t}" required></label>
        </div>
        <label class="field"><span>Repeat</span><select class="input" name="repeat">
          ${Object.entries(REPEAT_LABEL).map(([k, l]) => `<option value="${k}" ${(reminder?.repeat || 'none') === k ? 'selected' : ''}>${l}</option>`).join('')}
        </select></label>
        <label class="field"><span>Notes</span><textarea class="input" name="notes" maxlength="1000" placeholder="Dosage, instructions… (optional)">${esc(reminder?.notes)}</textarea></label>`,
      onSubmit: async f => {
        const data = { title: val(f, 'title'), pet_id: val(f, 'pet_id') || null, due_at: `${val(f, 'date')}T${val(f, 'time')}`, repeat: val(f, 'repeat'), notes: val(f, 'notes') };
        if (!val(f, 'date') || !val(f, 'time')) throw new Error('Pick a date and time.');
        if (reminder) await api('PUT', `/api/reminders/${reminder.id}`, data);
        else await api('POST', '/api/reminders', data);
        toast(reminder ? 'Reminder updated' : 'Reminder added');
        route();
      },
    });
    form.querySelectorAll('.suggest button').forEach(b => b.addEventListener('click', () => {
      form.elements.title.value = b.dataset.title;
      form.elements.repeat.value = b.dataset.repeat;
    }));
  }

  function confirmModal(title, text, label, action) {
    openModal({ title, submit: label, danger: true, body: `<p>${esc(text)}</p>`, onSubmit: action });
  }

  async function calendarModal() {
    const { path } = await api('GET', '/api/calendar');
    if (window.PETREM_STATIC) {
      const form = openModal({
        title: 'Sync with your calendar',
        body: `<p>When PetRem runs on a server, you get a private link that keeps Google, Apple or Outlook calendars in sync automatically.</p>
          <p>This live demo runs entirely in your browser, so download the calendar file instead and open it to import every vaccine due date and reminder.</p>
          <button type="button" class="btn primary" data-ics>${icon('calendar')}Download petrem.ics</button>`,
      });
      form.querySelector('[data-ics]').addEventListener('click', async () => {
        const text = await (await fetch(path)).text();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([text], { type: 'text/calendar' }));
        a.download = 'petrem.ics';
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 5000);
      });
      return;
    }
    const url = location.origin + path;
    const form = openModal({
      title: 'Sync with your calendar',
      body: `<p>Subscribe to this private link and every vaccine due date and reminder appears in your calendar, updating automatically.</p>
        <div class="copy-row"><input class="input" readonly value="${esc(url)}" aria-label="Calendar link"><button type="button" class="btn" data-copy>${icon('copy')}Copy</button></div>
        <ol class="steps">
          <li><b>Google Calendar:</b> Other calendars → + → From URL, then paste the link.</li>
          <li><b>Apple Calendar:</b> File → New Calendar Subscription, then paste the link.</li>
          <li><b>Outlook:</b> Add calendar → Subscribe from web.</li>
        </ol>
        <p class="disclaimer">Keep this link private: anyone with it can see your pets' schedule. Online calendars need PetRem to be deployed at a public address; <a href="${esc(path)}">download the .ics file</a> to import it once instead.</p>`,
    });
    const input = form.querySelector('.copy-row input');
    form.querySelector('[data-copy]').addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(url); toast('Link copied'); }
      catch { input.select(); toast('Press Ctrl/⌘ + C to copy'); }
    });
  }

  // ---------- auth ----------

  function renderAuth(mode = 'login') {
    document.title = 'PetRem · Pet care reminders';
    app.innerHTML = `<div class="auth">
      <section class="auth-art">
        <a class="logo" href="#/"><img src="static/icon.svg" alt="">PetRem</a>
        <div>
          <h1>Never miss a vaccine again.</h1>
          <p>Keep every pet's vaccinations, medication and care routine in one place, with reminders that show up before they're due.</p>
          <ul class="perks">
            <li><span class="dot">${icon('syringe')}</span>Vaccine plans built from each pet's age and species</li>
            <li><span class="dot">${icon('repeat')}</span>Repeating reminders for pills, flea treatments and walks</li>
            <li><span class="dot">${icon('calendar')}</span>Syncs with Google, Apple and Outlook calendars</li>
          </ul>
          <div class="preview-card"><span class="ava c4">B<span class="sp">${icon('paw')}</span></span><div><b>Biscuit · Rabies</b><div class="sub">First dose at 16 weeks</div></div><span class="pill due_soon">In 3 days</span></div>
        </div>
        <small>For general guidance only. Always follow your veterinarian's advice.</small>
      </section>
      <section class="auth-form"><div class="auth-card">
        <a class="logo" href="#/"><img src="static/icon.svg" alt="">PetRem</a>
        <h2>${mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
        <p>${mode === 'login' ? 'Log in to see what your pets need today.' : 'It takes a minute. Add your first pet right after.'}</p>
        <div class="tabs" role="tablist">
          <button type="button" class="${mode === 'login' ? 'on' : ''}" data-mode="login" role="tab" aria-selected="${mode === 'login'}">Log in</button>
          <button type="button" class="${mode === 'signup' ? 'on' : ''}" data-mode="signup" role="tab" aria-selected="${mode === 'signup'}">Sign up</button>
        </div>
        <form class="stack" id="auth-form" novalidate>
          <div class="form-error" hidden></div>
          ${mode === 'signup' ? '<label class="field"><span>Your name</span><input class="input" name="name" autocomplete="name" maxlength="60" required></label>' : ''}
          <label class="field"><span>Email</span><input class="input" type="email" name="email" autocomplete="email" required></label>
          <label class="field"><span>Password</span><input class="input" type="password" name="password" autocomplete="${mode === 'login' ? 'current-password' : 'new-password'}" minlength="8" required>${mode === 'signup' ? '<small>At least 8 characters.</small>' : ''}</label>
          <button class="btn primary" type="submit">${mode === 'login' ? 'Log in' : 'Create account'}</button>
          ${state.config.demo ? `<div class="or">or</div><button class="btn" type="button" id="demo-btn">${icon('spark')}Explore the demo account</button>` : ''}
        </form>
      </div></section>
    </div>`;
    app.querySelectorAll('[data-mode]').forEach(b => b.addEventListener('click', () => renderAuth(b.dataset.mode)));
    const form = document.getElementById('auth-form');
    const err = form.querySelector('.form-error');
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const btn = form.querySelector('[type=submit]');
      btn.disabled = true;
      err.hidden = true;
      try {
        const body = { email: val(form, 'email'), password: val(form, 'password') };
        if (mode === 'signup') body.name = val(form, 'name');
        const res = await api('POST', mode === 'login' ? '/api/login' : '/api/signup', body);
        state.me = res.user;
        location.hash = '#/today';
        route();
      } catch (e2) {
        err.textContent = e2.message;
        err.hidden = false;
        btn.disabled = false;
      }
    });
    document.getElementById('demo-btn')?.addEventListener('click', async () => {
      try {
        state.me = (await api('POST', '/api/demo')).user;
        location.hash = '#/today';
        route();
      } catch (e2) { err.textContent = e2.message; err.hidden = false; }
    });
    form.querySelector('input')?.focus();
  }

  // ---------- shell ----------

  function shell(active) {
    if (!document.getElementById('view')) {
      app.innerHTML = `<header class="top"><div class="top-in">
        <a class="logo" href="#/today"><img src="static/icon.svg" alt="">PetRem</a>
        <nav class="nav" aria-label="Main">
          <a href="#/today" data-nav="today">${icon('home')}Today</a>
          <a href="#/pets" data-nav="pets">${icon('paw')}Pets</a>
          <a href="#/reminders" data-nav="reminders">${icon('list')}Reminders</a>
        </nav>
        <div class="top-right">
          <button class="btn ghost icon bell" data-action="toggle-notes" aria-label="Notifications">${icon('bell')}<span class="badge" id="badge" hidden></span></button>
          <button class="avatar-btn" data-action="toggle-menu" aria-label="Account menu"></button>
          <div class="panel" id="notes-panel" hidden></div>
          <div class="menu" id="menu" hidden></div>
        </div>
      </div></header><main class="view" id="view"></main>`;
    }
    app.querySelector('.avatar-btn').textContent = (state.me.name[0] || '?').toUpperCase();
    document.getElementById('menu').innerHTML = `<div class="who"><b>${esc(state.me.name)}</b><span>${esc(state.me.email)}</span></div>
      <button data-action="calendar">${icon('calendar')}Sync with calendar</button>
      <button data-action="logout">${icon('logout')}Log out</button>`;
    app.querySelectorAll('[data-nav]').forEach(a => a.classList.toggle('on', a.dataset.nav === active));
    hidePopovers();
    return document.getElementById('view');
  }

  function hidePopovers() {
    document.getElementById('menu')?.setAttribute('hidden', '');
    document.getElementById('notes-panel')?.setAttribute('hidden', '');
  }

  async function loadNotes() {
    if (!state.me) return;
    try {
      state.notes = await api('GET', '/api/notifications');
    } catch { return; }
    const badge = document.getElementById('badge');
    if (badge) { badge.textContent = state.notes.unread > 9 ? '9+' : state.notes.unread; badge.hidden = !state.notes.unread; }
    const fresh = state.notes.items.filter(n => !n.read && n.id > state.lastAlerted);
    if (fresh.length && 'Notification' in window && Notification.permission === 'granted' && state.lastAlerted) {
      fresh.slice(0, 3).forEach(n => new Notification(n.title, { body: n.body, icon: 'static/icon.svg', tag: `petrem-${n.id}` }));
    }
    state.lastAlerted = Math.max(state.lastAlerted, ...state.notes.items.map(n => n.id), 0) || state.lastAlerted || 1;
  }

  function renderNotesPanel() {
    const panel = document.getElementById('notes-panel');
    const canAsk = 'Notification' in window && Notification.permission === 'default';
    panel.innerHTML = `<div class="panel-head"><h3>Notifications</h3>${canAsk ? `<button class="btn sm" data-action="enable-alerts">${icon('bell')}Desktop alerts</button>` : ''}</div>
      <div class="panel-list">${state.notes.items.length ? state.notes.items.map(n => `<a class="note ${n.read ? '' : 'unread'}" href="${esc(n.link || '#/today')}">
        <span class="ic">${icon(n.link.startsWith('#/pets') ? 'syringe' : 'bell')}</span><div><b>${esc(n.title)}</b><span>${esc(n.body)}</span></div></a>`).join('')
        : `<div class="empty-note">You're all caught up.</div>`}</div>`;
  }

  // ---------- views ----------

  async function viewToday(view) {
    const hour = new Date().getHours();
    const greet = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
    const dateText = new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' });
    view.innerHTML = `<div class="page-head"><div><p class="eyebrow">${esc(dateText)}</p><h1>${greet}, ${esc(firstName(state.me.name))}</h1></div>
      <div class="head-actions"><button class="btn" data-action="add-pet">${icon('plus')}Add pet</button><button class="btn primary" data-action="add-reminder">${icon('plus')}New reminder</button></div></div>
      ${skeleton(3)}`;
    const d = await api('GET', '/api/dashboard');
    document.title = d.counts.overdue ? `(${d.counts.overdue}) PetRem` : 'PetRem';
    const head = view.querySelector('.page-head').outerHTML;
    if (!d.counts.pets && !d.overdue.length && !d.due_today.length && !d.upcoming.length) {
      view.innerHTML = head + empty('paw', 'Add your first pet', "Tell us about your pet and we'll build their vaccination plan and remind you before anything is due.",
        `<button class="btn primary" data-action="add-pet">${icon('plus')}Add a pet</button>`);
      return;
    }
    const section = (title, items, emptyHtml = '') => `<section class="section"><div class="section-head"><h2>${title}</h2><span class="count">${items.length}</span></div>
      ${items.length ? `<div class="list">${items.map(agendaItem).join('')}</div>` : emptyHtml}</section>`;
    view.innerHTML = head + `
      <div class="tiles">
        <div class="tile ${d.counts.overdue ? 'alert' : ''}"><b>${d.counts.overdue}</b><span>Overdue</span></div>
        <div class="tile ${d.counts.today ? 'sun' : ''}"><b>${d.counts.today}</b><span>Due today</span></div>
        <div class="tile"><b>${d.counts.week}</b><span>Next 7 days</span></div>
        <div class="tile"><b>${d.counts.pets}</b><span>${d.counts.pets === 1 ? 'Pet' : 'Pets'}</span></div>
      </div>
      ${d.overdue.length ? section('Overdue', d.overdue) : ''}
      ${section('Today', d.due_today, `<div class="all-clear">${icon('check')}Nothing due today. Enjoy the cuddles.</div>`)}
      ${section('Coming up', d.upcoming, `<p class="disclaimer">Nothing in the next 30 days.</p>`)}`;
  }

  async function viewPets(view) {
    view.innerHTML = `<div class="page-head"><div><p class="eyebrow">Your family</p><h1>Pets</h1></div>
      <div class="head-actions"><button class="btn primary" data-action="add-pet">${icon('plus')}Add pet</button></div></div>${skeleton(2)}`;
    const pets = await ensurePets(true);
    const head = view.querySelector('.page-head').outerHTML;
    if (!pets.length) {
      view.innerHTML = head + empty('paw', 'No pets yet', 'Add a dog, cat or any other companion to start tracking their care.',
        `<button class="btn primary" data-action="add-pet">${icon('plus')}Add your first pet</button>`);
      return;
    }
    view.innerHTML = head + `<div class="pet-grid">${pets.map(p => {
      const next = p.next
        ? `<span>${esc(p.next.name)}</span><span class="pill ${p.next.status}">${p.next.status === 'overdue' ? 'Overdue' : relDay(p.next.days) || fmtDate(p.next.due)}</span>`
        : `<span>No standard vaccines</span><span class="pill none">Use reminders</span>`;
      return `<a class="pet-card" href="#/pets/${p.id}"><div class="pet-top">${ava(p)}<div><h3>${esc(p.name)}</h3>
        <div class="sub">${esc([p.breed || SPECIES_LABEL[p.species], p.age].join(' · '))}</div></div></div>
        <div class="pet-next">${next}</div></a>`;
    }).join('')}<button class="add-card" data-action="add-pet">${icon('plus')}Add another pet</button></div>`;
  }

  async function viewPet(view, id) {
    view.innerHTML = `<a class="back" href="#/pets">${icon('back')}All pets</a>${skeleton(3)}`;
    let pet;
    try { pet = await api('GET', `/api/pets/${id}`); }
    catch (e) {
      if (e.status === 404) { view.innerHTML = `<a class="back" href="#/pets">${icon('back')}All pets</a>` + empty('paw', 'Pet not found', 'It may have been removed.'); return; }
      throw e;
    }
    state.currentPet = pet;
    document.title = `${pet.name} · PetRem`;
    const facts = [SPECIES_LABEL[pet.species], pet.breed, pet.sex && pet.sex[0].toUpperCase() + pet.sex.slice(1), `${pet.age} old`, pet.weight_kg ? `${pet.weight_kg} kg` : '', `Born ${fmtDate(pet.birth_date)}`].filter(Boolean);
    const vax = pet.vaccines.length
      ? pet.vaccines.map(v => {
        const dots = Array.from({ length: v.series }, (_, k) => `<i class="${k < v.series_done ? 'on' : ''}"></i>`).join('');
        const series = v.series_done < v.series ? `Initial series: ${v.series_done} of ${v.series}` : `Series complete · booster every ${v.booster_months} months`;
        const history = v.doses.length
          ? v.doses.map(d => `<span title="${esc(d.notes)}">${fmtDate(d.given_on)}<button data-action="del-dose" data-id="${d.id}" aria-label="Remove ${esc(v.name)} dose from ${fmtDate(d.given_on)}">${icon('x')}</button></span>`).join('')
          : '<span class="disclaimer">No doses recorded yet</span>';
        return `<article class="vax"><div class="vax-top"><div><h3>${esc(v.name)} ${v.core ? '' : '<span class="tag">Optional</span>'}</h3><p>${esc(v.protects)}</p></div>
          <span class="pill ${v.status}">${vaxStatus(v)}</span></div>
          <div class="progress">${dots}<span>${series}</span></div>
          <div class="vax-foot"><div class="history">${history}</div>
          <button class="btn sm ${v.status === 'overdue' ? 'primary' : ''}" data-action="add-dose" data-pet="${pet.id}" data-species="${pet.species}" data-vaccine="${v.code}">${icon('syringe')}Record dose</button></div></article>`;
      }).join('')
      : empty('heart', 'No standard vaccine schedule', `There's no built-in plan for this species. Add reminders for vet visits, medication and care.`,
        `<button class="btn primary" data-action="add-reminder" data-pet="${pet.id}">${icon('plus')}Add a reminder</button>`);
    const upcoming = pet.reminders.filter(r => !r.done_at);
    view.innerHTML = `<a class="back" href="#/pets">${icon('back')}All pets</a>
      <section class="pet-hero">${ava(pet, 'lg')}<div><h1>${esc(pet.name)}</h1><div class="facts">${facts.map(f => `<span>${esc(f)}</span>`).join('')}</div></div>
        <div class="head-actions"><button class="btn" data-action="edit-pet">${icon('edit')}Edit</button><button class="btn danger" data-action="delete-pet">${icon('trash')}Delete</button></div>
        ${pet.notes ? `<p class="pet-notes">${esc(pet.notes)}</p>` : ''}</section>
      <div class="cols">
        <section><div class="section-head"><h2>Vaccinations</h2>${pet.overdue ? `<span class="pill overdue">${pet.overdue} overdue</span>` : ''}</div>
          <div class="list">${vax}</div>
          ${pet.vaccines.length ? '<p class="disclaimer">Based on common guidelines for core and optional vaccines. Your vet may recommend a different schedule.</p>' : ''}</section>
        <section><div class="section-head"><h2>Reminders</h2><span class="count">${upcoming.length}</span>
          <button class="btn sm" data-action="add-reminder" data-pet="${pet.id}">${icon('plus')}Add</button></div>
          ${upcoming.length ? `<div class="list">${upcoming.map(reminderRow).join('')}</div>` : '<p class="disclaimer">No reminders for this pet yet.</p>'}</section>
      </div>`;
  }

  async function viewReminders(view) {
    view.innerHTML = `<div class="page-head"><div><p class="eyebrow">Care routine</p><h1>Reminders</h1></div>
      <div class="head-actions"><button class="btn primary" data-action="add-reminder">${icon('plus')}New reminder</button></div></div>${skeleton(3)}`;
    const data = await api('GET', '/api/reminders');
    const head = view.querySelector('.page-head').outerHTML;
    const list = state.tab === 'done' ? data.done : data.upcoming;
    view.innerHTML = head + `<div class="seg" role="tablist">
        <button class="${state.tab === 'upcoming' ? 'on' : ''}" data-action="tab" data-tab="upcoming">Upcoming · ${data.upcoming.length}</button>
        <button class="${state.tab === 'done' ? 'on' : ''}" data-action="tab" data-tab="done">Completed · ${data.done.length}</button></div>
      ${list.length ? `<div class="list">${list.map(reminderRow).join('')}</div>`
        : state.tab === 'done' ? empty('check', 'Nothing completed yet', 'Reminders you mark as done show up here.')
          : empty('bell', 'No reminders yet', 'Set up flea treatments, medication, walks or vet visits, once or on repeat.',
            `<button class="btn primary" data-action="add-reminder">${icon('plus')}Create a reminder</button>`)}`;
  }

  // ---------- router ----------

  const ROUTES = [
    [/^#\/today$/, 'today', v => viewToday(v)],
    [/^#\/pets$/, 'pets', v => viewPets(v)],
    [/^#\/pets\/(\d+)$/, 'pets', (v, m) => viewPet(v, +m[1])],
    [/^#\/reminders$/, 'reminders', v => viewReminders(v)],
  ];
  let renderSeq = 0;

  async function route() {
    const seq = ++renderSeq;
    if (!state.me) {
      try { state.me = (await api('GET', '/api/me')).user; } catch { state.me = null; }
      if (seq !== renderSeq) return;
    }
    if (!state.me) { renderAuth(); return; }
    const hash = location.hash || '#/today';
    const match = ROUTES.map(([re, nav, fn]) => [hash.match(re), nav, fn]).find(([m]) => m);
    if (!match) { location.replace('#/today'); return; }
    const [m, nav, fn] = match;
    const view = shell(nav);
    document.title = 'PetRem';
    try {
      await fn(view, m);
    } catch (e) {
      if (seq === renderSeq && state.me) view.innerHTML = empty('x', 'Something went wrong', e.message, `<button class="btn" data-action="retry">Try again</button>`);
    }
    loadNotes();
  }

  // ---------- events ----------

  document.addEventListener('click', async e => {
    const el = e.target.closest('[data-action]');
    if (!e.target.closest('#menu, #notes-panel, [data-action="toggle-menu"], [data-action="toggle-notes"]')) hidePopovers();
    if (e.target.closest('.note')) hidePopovers();
    if (!el) return;
    const { action, id, pet, species, vaccine } = el.dataset;
    try {
      switch (action) {
        case 'toggle-menu': {
          const menu = document.getElementById('menu');
          const open = menu.hidden;
          hidePopovers();
          menu.hidden = !open;
          break;
        }
        case 'toggle-notes': {
          const panel = document.getElementById('notes-panel');
          const open = panel.hidden;
          hidePopovers();
          if (!open) break;
          await loadNotes();
          renderNotesPanel();
          panel.hidden = false;
          if (state.notes.unread) {
            await api('POST', '/api/notifications/read');
            state.notes.unread = 0;
            document.getElementById('badge').hidden = true;
          }
          break;
        }
        case 'enable-alerts': {
          const result = await Notification.requestPermission();
          toast(result === 'granted' ? 'Desktop alerts are on' : 'Desktop alerts stay off');
          renderNotesPanel();
          break;
        }
        case 'logout':
          await api('POST', '/api/logout');
          Object.assign(state, { me: null, pets: null, notes: { items: [], unread: 0 }, lastAlerted: 0 });
          location.hash = '#/';
          renderAuth();
          break;
        case 'calendar': hidePopovers(); await calendarModal(); break;
        case 'add-pet': petForm(); break;
        case 'edit-pet': petForm(state.currentPet); break;
        case 'delete-pet': {
          const p = state.currentPet;
          confirmModal(`Delete ${p.name}?`, `This permanently removes ${p.name}, their vaccine history and their reminders.`, `Delete ${p.name}`, async () => {
            await api('DELETE', `/api/pets/${p.id}`);
            state.pets = null;
            toast(`${p.name} was removed`);
            location.hash = '#/pets';
          });
          break;
        }
        case 'add-dose': await doseForm(+pet, species, vaccine); break;
        case 'del-dose':
          await api('DELETE', `/api/doses/${id}`);
          toast('Dose removed');
          route();
          break;
        case 'add-reminder': await reminderForm(null, pet ? +pet : null); break;
        case 'edit-reminder': await reminderForm(state.reminders.get(+id)); break;
        case 'done-reminder': {
          el.disabled = true;
          const r = await api('POST', `/api/reminders/${id}/complete`);
          toast(r.done_at ? `Nice, "${r.title}" is done` : `Done. Next one: ${whenLabel(...r.due_at.split('T')).text}`);
          route();
          break;
        }
        case 'del-reminder': {
          const r = state.reminders.get(+id);
          confirmModal('Delete reminder?', `"${r?.title}" will be removed${r?.repeat !== 'none' ? ', including future repeats' : ''}.`, 'Delete', async () => {
            await api('DELETE', `/api/reminders/${id}`);
            toast('Reminder deleted');
            route();
          });
          break;
        }
        case 'tab': state.tab = el.dataset.tab; route(); break;
        case 'retry': route(); break;
      }
    } catch (err) {
      el.disabled = false;
      toast(err.message, 'err');
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeModal(); hidePopovers(); }
  });
  window.addEventListener('hashchange', () => { closeModal(); route(); });
  setInterval(loadNotes, 60000);

  api('GET', '/api/config').then(c => { state.config = c; }).catch(() => {}).finally(route);
})();
