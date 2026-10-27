/*
 * BookForge phone UI — same look and feel as VOX.
 * Library (compiled audiobooks + the running job), Listen (player), Settings (PC address).
 */

/* ---------- server address (works when served by the PC and inside a native app) ---------- */
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
  del(k) { try { localStorage.removeItem(k); } catch { /* ignore */ } },
};
const native = !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
const servedByPC = !native && /^https?:$/.test(location.protocol) && !!location.port;
/* the PC whose QR code was scanned last (or typed in Settings); the page's own PC when the PC serves it */
let SERVER = (store.get('bf:server', '') || (servedByPC ? location.origin : '')).replace(/\/+$/, '');
const api = (path) => SERVER + path;

/* ---------- icons (VOX 24px line set) ---------- */
const P = {
  plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  library: '<path d="M4 19.5V5a2 2 0 0 1 2-2h3v18H6a2 2 0 0 1-2-1.5Z"/><path d="M9 3h4v18H9z"/><path d="m15 4.2 3.6-.9 3.2 16.6-3.6.8z"/>',
  player: '<circle cx="12" cy="12" r="9"/><path d="m10 8.5 5.5 3.5-5.5 3.5z"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
  more: '<circle cx="12" cy="5.5" r="1.4" fill="currentColor"/><circle cx="12" cy="12" r="1.4" fill="currentColor"/><circle cx="12" cy="18.5" r="1.4" fill="currentColor"/>',
  download: '<path d="M12 4v11"/><path d="m7 10 5 5 5-5"/><path d="M5 20h14"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>',
  wave: '<path d="M3 12h2M7 8v8M11 5v14M15 9v6M19 7v10"/>',
  trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  close: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  back15: '<path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 4v4.5h4.5"/><text x="12.2" y="15.3" font-size="7.5" font-weight="700" text-anchor="middle" fill="currentColor" stroke="none" font-family="system-ui">15</text>',
  fwd30: '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 4v4.5h-4.5"/><text x="11.8" y="15.3" font-size="7.5" font-weight="700" text-anchor="middle" fill="currentColor" stroke="none" font-family="system-ui">30</text>',
  speaker: '<path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/>',
  qr: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><path d="M14 14h3v3h-3zM20 14v.01M14 20h.01M17 17h4v4h-4"/>',
  text: '<path d="M4 6h16M4 10h16M4 14h11M4 18h8"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2.5"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
  phone: '<rect x="6" y="2.5" width="12" height="19" rx="2.5"/><path d="M11 18h2"/>',
  share: '<path d="M12 15V3"/><path d="m7 8 5-5 5 5"/><path d="M20 15v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-4"/>',
};
const FILLED = {
  play: '<path d="M7 4.8v14.4a1 1 0 0 0 1.5.9l11.2-7.2a1 1 0 0 0 0-1.8L8.5 3.9A1 1 0 0 0 7 4.8Z"/>',
  pause: '<rect x="6" y="4.5" width="4.2" height="15" rx="1.2"/><rect x="13.8" y="4.5" width="4.2" height="15" rx="1.2"/>',
};
function icon(name, size = 22) {
  const filled = name in FILLED;
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true" fill="${filled ? 'currentColor' : 'none'}"` +
    ` stroke="${filled ? 'none' : 'currentColor'}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${filled ? FILLED[name] : P[name]}</svg>`;
}
const SIZES = { playBtn: 30, miniBtn: 20, tab: 23, ctrl: 26 };
function paintIcons(root = document) {
  root.querySelectorAll('[data-icon]').forEach((n) => {
    const size = Object.keys(SIZES).find((c) => n.classList.contains(c) || (n.parentElement && n.parentElement.classList.contains(c)));
    n.innerHTML = icon(n.dataset.icon, size ? SIZES[size] : 22);
  });
}
function setIcon(btn, name) { btn.dataset.icon = name; paintIcons(btn.parentElement); }

/* ---------- helpers ---------- */
const $ = (id) => document.getElementById(id);
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
function clock(sec) {
  sec = Math.max(0, Math.floor(sec || 0));
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  return h ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}` : `${m}:${String(s).padStart(2, '0')}`;
}
function human(sec) {
  sec = Math.round(sec || 0);
  if (sec < 60) return `${sec}s`;
  const h = Math.floor(sec / 3600), m = Math.round((sec % 3600) / 60);
  return h ? `${h} h ${m} min` : `${m} min`;
}
const prettyTitle = (name) => name.replace(/\.(m4b|mp3|zip)$/i, '').replace(/_[0-9a-f]{8}$/i, '').replace(/_/g, ' ').trim();

let toastTimer;
function toast(msg) {
  $('toast-text').textContent = msg;
  $('toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $('toast').hidden = true; }, 6000);
}
$('toast').onclick = () => { $('toast').hidden = true; };

async function getJSON(path, opts) {
  const res = await fetch(api(path), opts);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { msg = (await res.json()).detail || msg; } catch { /* not json */ }
    throw new Error(msg);
  }
  return res.json();
}

/* ---------- generated covers (same palettes as VOX) ---------- */
const PALETTES = [
  ['#c0643c', '#e8a67c'], ['#6f8462', '#b5c49d'], ['#3f5a6e', '#8fa9bb'],
  ['#8a4f6a', '#d2a0b5'], ['#b38a2e', '#e6cb83'], ['#4f7a74', '#9fc6bd'], ['#6b5847', '#c4ab91'],
];
function hash(s) { let h = 7; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }
function cover(title = 'Untitled', size = 'md', img) {
  const h = hash(title);
  const [a, b] = PALETTES[h % PALETTES.length];
  const n = el('div', `cover cover-${size} pattern-${h % 3}`);
  n.style.setProperty('--c1', a);
  n.style.setProperty('--c2', b);
  n.append(el('span', 'coverTitle', title), el('span', 'coverMark', 'BOOKFORGE'));
  if (img) {
    const i = new Image();
    i.alt = '';
    i.onload = () => n.append(i);
    i.src = img;
  }
  return n;
}

/* ---------- sheets ---------- */
function openSheet(id) { $(id).hidden = false; }
function closeSheet(id) { $(id).hidden = true; }
document.querySelectorAll('.sheetBackdrop').forEach((b) => {
  b.addEventListener('click', (e) => { if (e.target === b) b.hidden = true; });
});

/* ---------- tabs ---------- */
let tab = 'library';
function showTab(t) {
  tab = t;
  document.querySelectorAll('.tab').forEach((b) => b.classList.toggle('on', b.dataset.tab === t));
  document.querySelectorAll('[data-page]').forEach((p) => { p.hidden = p.dataset.page !== t; });
  $('view').scrollTop = 0;
  if (t === 'library') loadLibrary();
  if (t === 'settings') loadServerInfo();
  updateMini();
}
document.querySelectorAll('.tab').forEach((b) => { b.onclick = () => showTab(b.dataset.tab); });

/* ================= LIBRARY ================= */
let books = [];        // on the PC
let pcOnline = false;

async function loadLibrary() {
  if (!SERVER) { pcOnline = false; books = []; renderShelf(); return; }
  try {
    books = await getJSON('/api/audiobooks');
    pcOnline = true;
  } catch {
    books = [];
    pcOnline = false;
    if ($('job-card').hidden && !Object.keys(saved).length) toast(`Can't reach the PC at ${SERVER}. Check Wi-Fi, or scan its code again in Settings.`);
  }
  renderShelf();
}

/* what the shelf shows: books on the PC plus books saved on this phone (those stay when the PC is off) */
function shelfBooks() {
  const list = books.map((b) => ({ ...b, ...(saved[b.filename] ? { saved: true } : {}) }));
  for (const [filename, m] of Object.entries(saved)) {
    if (!list.some((b) => b.filename === filename)) list.push({ filename, format: m.format, size_mb: m.size_mb, duration_sec: m.duration_sec, saved: true, phoneOnly: true });
  }
  return list;
}

function renderShelf() {
  const shelf = $('shelf');
  shelf.replaceChildren();
  const list = shelfBooks();
  $('shelf-title').hidden = !list.length;
  $('empty').hidden = !!list.length || !$('job-card').hidden || !$('importing').hidden;
  $('btn-scan-empty').textContent = SERVER && pcOnline ? 'Connect to a different PC — scan its code' : 'Connect to your PC — scan its code';
  for (const b of list) {
    const title = prettyTitle(b.filename);
    const item = el('div', 'shelfItem');
    const wrap = el('div', 'shelfCover');
    const pct = saving[b.filename];
    const tag = pct != null ? el('span', 'fmtTag saving', `SAVING ${Math.round(pct * 100)}%`)
      : b.saved ? el('span', 'fmtTag saved', '✓ ON PHONE') : el('span', 'fmtTag', b.format.toUpperCase());
    tag.dataset.tag = b.filename;
    wrap.append(cover(title, 'sm'), tag);
    const more = el('button', 'moreBtn');
    more.setAttribute('aria-label', 'Options');
    more.innerHTML = icon('more', 18);
    more.onclick = (e) => { e.stopPropagation(); bookMenu(b); };
    wrap.append(more);
    const pos = store.get('bf:pos:' + b.filename, 0);
    const bits = [b.duration_sec ? human(b.duration_sec) : null, `${b.size_mb} MB`];
    if (pos > 5 && b.duration_sec) bits[0] = `${Math.round((pos / b.duration_sec) * 100)}% · ${human(b.duration_sec)}`;
    item.append(wrap, el('b', null, title), el('span', null, bits.filter(Boolean).join(' · ')));
    item.onclick = () => (b.format === 'zip' ? bookMenu(b) : play(b));
    shelf.append(item);
  }
}

function bookMenu(b) {
  const title = prettyTitle(b.filename);
  $('menu-title').textContent = title;
  const rows = $('menu-rows');
  rows.replaceChildren();
  const row = (ic, label, sub, fn, danger) => {
    const r = el('button', 'sheetRow' + (danger ? ' danger' : ''));
    const i = el('span', 'sheetIcon');
    i.innerHTML = icon(ic);
    const t = el('span');
    t.append(el('b', null, label), el('em', null, sub));
    r.append(i, t);
    r.onclick = () => fn(r);
    rows.append(r);
    return r;
  };
  const isSaved = !!saved[b.filename];
  if (b.format !== 'zip') row('play', 'Listen', isSaved ? 'From this phone — works offline' : 'Streams from the PC', () => { closeSheet('menu-sheet'); play(b); });
  if (!isSaved && saving[b.filename] == null) {
    row('phone', 'Save to phone', `Keep it in BookForge to play offline · ${b.size_mb} MB`, () => { closeSheet('menu-sheet'); saveBook(b); });
  }
  if (isSaved) {
    row('share', native ? 'Share or export' : 'Export to Downloads', 'Open it in another app or keep a copy', () => { closeSheet('menu-sheet'); exportBook(b.filename); });
    let armedLocal = false;
    row('trash', 'Remove from phone', b.phoneOnly ? 'Gone from the PC too — this deletes it for good' : 'Still on the PC — you can save it again', async (r) => {
      if (!armedLocal) { armedLocal = true; r.querySelector('b').textContent = 'Tap again to remove'; return; }
      await unsaveBook(b.filename);
      if (now && now.filename === b.filename && b.phoneOnly) stopPlayer();
      closeSheet('menu-sheet');
      toast(`Removed “${title}” from this phone.`);
      renderShelf();
    }, true);
  }
  if (b.phoneOnly || !pcOnline) { openSheet('menu-sheet'); return; }
  if (!isSaved) row('download', 'Download file', `${b.format === 'zip' ? 'MP3 tracks in a .zip' : '.' + b.format + ' file'} to the phone's Downloads`, () => { closeSheet('menu-sheet'); download(b.filename); });
  let armed = false;
  row('trash', 'Delete from PC', isSaved ? 'The copy on this phone stays' : 'Save it to the phone first to keep it', async (r) => {
    if (!armed) { armed = true; r.querySelector('b').textContent = 'Tap again to delete'; return; }
    try {
      await getJSON('/api/audiobooks/' + encodeURIComponent(b.filename), { method: 'DELETE' });
      store.del('bf:pos:' + b.filename);
      if (now && now.filename === b.filename) stopPlayer();
      closeSheet('menu-sheet');
      toast(`Deleted “${title}”.`);
      loadLibrary();
    } catch (e) { toast('Could not delete: ' + e.message); }
  }, true);
  openSheet('menu-sheet');
}

function download(filename) {
  const a = document.createElement('a');
  a.href = api('/api/download/' + encodeURIComponent(filename));
  a.download = filename;
  document.body.append(a);
  a.click();
  a.remove();
  toast('Downloading to your phone — find it in Downloads.');
}

/* ================= SAVED ON THIS PHONE =================
 * Native app: plain files in the app's private storage (Capacitor Filesystem) — no browser quota.
 * Browser: Blobs in IndexedDB. Either way the book then plays with the PC off.
 */
const Cap = native ? window.Capacitor : null;
const FS = native ? (Cap.Plugins.Filesystem || Cap.registerPlugin('Filesystem')) : null;
const Share = native ? (Cap.Plugins.Share || Cap.registerPlugin('Share')) : null;
const DIR = 'audiobooks';
let saved = store.get('bf:saved', {});    // filename → { format, size_mb, duration_sec, savedAt }
const saving = {};                        // filename → 0..1 while downloading

let dbp = null;
function db() {
  dbp ||= new Promise((resolve, reject) => {
    const r = indexedDB.open('bookforge', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('books');
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => { dbp = null; reject(r.error); };
  });
  return dbp;
}
async function idb(mode, fn) {
  const d = await db();
  return new Promise((resolve, reject) => {
    const t = d.transaction('books', mode);
    const req = fn(t.objectStore('books'));
    t.oncomplete = () => resolve(req.result);
    t.onerror = t.onabort = () => reject(t.error || new Error('storage failed'));
  });
}
function toBase64(bytes) {
  let bin = '';
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

function showSaving(filename) {
  const tag = document.querySelector(`[data-tag="${CSS.escape(filename)}"]`);
  if (tag && saving[filename] != null) tag.textContent = `SAVING ${Math.round(saving[filename] * 100)}%`;
}

async function saveBook(b) {
  const fn = b.filename;
  if (saving[fn] != null || saved[fn]) return;
  saving[fn] = 0;
  renderShelf();
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
  try {
    const res = await fetch(api('/api/download/' + encodeURIComponent(fn)));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const total = Number(res.headers.get('Content-Length')) || b.size_mb * 1048576;
    const reader = res.body.getReader();
    let loaded = 0, last = 0;
    const tick = () => { saving[fn] = Math.min(0.99, loaded / total); if (Date.now() - last > 300) { last = Date.now(); showSaving(fn); } };
    if (native) {
      /* write as it arrives, 3 MB at a time — a whole book in memory (and in base64) would crash a phone */
      const tmp = `${DIR}/${fn}.part`;
      let buf = [], bufLen = 0, first = true;
      const flush = async () => {
        if (!bufLen) return;
        const chunk = new Uint8Array(bufLen);
        let off = 0;
        for (const p of buf) { chunk.set(p, off); off += p.length; }
        buf = []; bufLen = 0;
        const data = toBase64(chunk);
        if (first) { await FS.writeFile({ path: tmp, data, directory: 'DATA', recursive: true }); first = false; }
        else await FS.appendFile({ path: tmp, data, directory: 'DATA' });
      };
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf.push(value); bufLen += value.length; loaded += value.length;
        if (bufLen >= 3 * 1048576) await flush();
        tick();
      }
      await flush();
      try { await FS.deleteFile({ path: `${DIR}/${fn}`, directory: 'DATA' }); } catch { /* none yet */ }
      await FS.rename({ from: tmp, to: `${DIR}/${fn}`, directory: 'DATA', toDirectory: 'DATA' });
    } else {
      const parts = [];
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        parts.push(value); loaded += value.length;
        tick();
      }
      await idb('readwrite', (s) => s.put(new Blob(parts, { type: fn.endsWith('.zip') ? 'application/zip' : 'audio/mp4' }), fn));
    }
    /* the read-along text goes with it, so words still follow along offline */
    let hasText = false;
    try {
      const tr = await fetch(api('/api/transcript/' + encodeURIComponent(fn)));
      if (tr.ok) {
        const json = await tr.text();
        if (native) await FS.writeFile({ path: `${DIR}/${fn}.words.json`, data: json, directory: 'DATA', encoding: 'utf8', recursive: true });
        else await idb('readwrite', (s) => s.put(json, fn + '#text'));
        hasText = true;
      }
    } catch { /* audio is saved; text can stream later */ }
    saved[fn] = { format: b.format, size_mb: b.size_mb, duration_sec: b.duration_sec, savedAt: Date.now(), hasText };
    store.set('bf:saved', saved);
    toast(`“${prettyTitle(fn)}” is saved on this phone.`);
  } catch (e) {
    toast(`Couldn't save “${prettyTitle(fn)}”: ${e.message}`);
  } finally {
    delete saving[fn];
    renderShelf();
    showStorage();
  }
}

async function unsaveBook(fn) {
  try {
    if (native) await FS.deleteFile({ path: `${DIR}/${fn}`, directory: 'DATA' });
    else await idb('readwrite', (s) => s.delete(fn));
  } catch { /* already gone */ }
  try {
    if (native) await FS.deleteFile({ path: `${DIR}/${fn}.words.json`, directory: 'DATA' });
    else await idb('readwrite', (s) => s.delete(fn + '#text'));
  } catch { /* had no text */ }
  if (localUrls[fn]) { URL.revokeObjectURL(localUrls[fn]); delete localUrls[fn]; }
  delete saved[fn];
  store.set('bf:saved', saved);
  showStorage();
}

/* a URL the <audio> element can play from this phone */
const localUrls = {};
async function localUrl(fn) {
  if (native) {
    const { uri } = await FS.getUri({ path: `${DIR}/${fn}`, directory: 'DATA' });
    return Cap.convertFileSrc(uri);
  }
  if (localUrls[fn]) return localUrls[fn];
  const blob = await idb('readonly', (s) => s.get(fn));
  if (!blob) throw new Error('not on this phone any more');
  return (localUrls[fn] = URL.createObjectURL(blob));
}

async function exportBook(fn) {
  try {
    if (native) {
      const { uri } = await FS.getUri({ path: `${DIR}/${fn}`, directory: 'DATA' });
      await Share.share({ title: prettyTitle(fn), files: [uri] });
      return;
    }
    const a = document.createElement('a');
    a.href = await localUrl(fn);
    a.download = fn;
    document.body.append(a);
    a.click();
    a.remove();
  } catch (e) {
    if (!/cancel/i.test(e.message || '')) toast("Couldn't export: " + e.message);
  }
}

function showStorage() {
  const list = Object.values(saved);
  $('st-saved').textContent = list.length;
  $('st-space').textContent = `${list.reduce((s, m) => s + (m.size_mb || 0), 0).toFixed(0)} MB`;
}
$('auto-save').checked = store.get('bf:autosave', true);
$('auto-save').onchange = () => store.set('bf:autosave', $('auto-save').checked);

/* ---------- add a book ---------- */
const pick = () => $('file-input').click();
$('btn-add').onclick = pick;
$('btn-add-empty').onclick = pick;
$('file-input').onchange = () => {
  const f = $('file-input').files[0];
  $('file-input').value = '';
  if (f) upload(f);
};

let book = null;
async function upload(file) {
  $('importing-name').textContent = `Reading “${file.name}”…`;
  $('importing').hidden = false;
  $('empty').hidden = true;
  showTab('library');
  const fd = new FormData();
  fd.append('file', file);
  try {
    book = await getJSON('/api/upload', { method: 'POST', body: fd });
    openBookSheet(book);
  } catch (e) {
    toast(`Couldn't read that book: ${e.message}`);
  } finally {
    $('importing').hidden = true;
    renderShelf();
  }
}

/* ---------- book setup sheet ---------- */
let voices = { kokoro: [], edge: [] };
let voice = store.get('bf:voice', 'af_heart');
let format = 'm4b';

async function loadVoices() {
  try {
    const d = await getJSON('/api/voices');
    voices = { kokoro: d.kokoro_voices || [], edge: d.edge_voices || [] };
  } catch { /* offline — sheet shows the saved choice */ }
  showVoice();
}
const voiceInfo = (id) => voices.kokoro.find((v) => v.id === id) || voices.edge.find((v) => v.id === id);
const isCloud = (id) => /Neural$/.test(id);

function showVoice() {
  const v = voiceInfo(voice) || { name: voice, desc: '' };
  const name = v.name.replace(/\s*\(.*\)$/, '');
  $('bk-voice-av').textContent = name[0] || '?';
  $('bk-voice-name').textContent = name;
  $('bk-voice-desc').textContent = isCloud(voice) ? `${v.accent} ${v.gender.toLowerCase()} · online, needs internet on the PC` : `${v.accent || ''} ${(v.gender || '').toLowerCase()} · ${v.desc || ''}`;
}

function openBookSheet(b) {
  const holder = $('bk-cover');
  holder.replaceChildren(cover(b.title, 'xs', b.cover_path ? api(`/api/books/${b.book_id}/cover`) : null));
  $('bk-title').textContent = b.title;
  $('bk-meta').textContent = `${b.author && b.author !== 'Unknown Author' ? b.author + ' · ' : ''}${b.format.toUpperCase()} · ${b.total_words.toLocaleString()} words · about ${human(b.estimated_duration_sec)} of audio`;
  const list = $('bk-chapters');
  list.replaceChildren();
  for (const c of b.chapters) {
    const row = el('label', 'chap');
    const cb = el('input');
    cb.type = 'checkbox';
    cb.checked = c.selected !== false;
    cb.dataset.id = c.id;
    cb.onchange = countChapters;
    const tick = el('span', 'tick');
    tick.innerHTML = icon('check', 15);
    const t = el('span', 'listText');
    t.append(el('b', null, c.title), el('em', null, `${c.word_count.toLocaleString()} words`));
    row.append(cb, tick, t);
    list.append(row);
  }
  countChapters();
  showVoice();
  openSheet('book-sheet');
}

function countChapters() {
  const all = $('bk-chapters').querySelectorAll('input');
  const on = [...all].filter((c) => c.checked).length;
  $('bk-chap-count').textContent = `${on} of ${all.length}`;
  $('bk-toggle').textContent = on === all.length ? 'Select none' : 'Select all';
  $('bk-start').disabled = !on;
}
$('bk-toggle').onclick = () => {
  const all = [...$('bk-chapters').querySelectorAll('input')];
  const target = !all.every((c) => c.checked);
  all.forEach((c) => { c.checked = target; });
  countChapters();
};

$('bk-speed').value = store.get('bf:rate', 1);
const showRate = () => { $('bk-speed-val').textContent = `${Number($('bk-speed').value).toFixed(2)}×`; };
$('bk-speed').oninput = showRate;
showRate();

$('bk-format').querySelectorAll('button').forEach((btn) => {
  btn.onclick = () => {
    format = btn.dataset.fmt;
    $('bk-format').querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === btn));
  };
});
$('bk-cancel').onclick = () => closeSheet('book-sheet');

/* ---------- narrator picker ---------- */
const sample = new Audio();
let sampling = null;
$('bk-voice').onclick = () => { renderVoices(); openSheet('voice-sheet'); };

function renderVoices() {
  const list = $('voice-list');
  list.replaceChildren();
  const groups = {};
  for (const v of voices.kokoro) (groups[`${v.accent} ${v.gender.toLowerCase()}`] ||= []).push(v);
  if (voices.edge.length) groups['Online voices · Microsoft'] = voices.edge;
  for (const [name, vs] of Object.entries(groups)) {
    list.append(el('div', 'groupLabel', name));
    const card = el('div', 'card list');
    for (const v of vs) {
      const row = el('div', 'listRow' + (v.id === voice ? ' on' : ''));
      row.style.cursor = 'pointer';
      const label = v.name.replace(/\s*\(.*\)$/, '');
      const t = el('span', 'listText');
      t.append(el('b', null, label), el('em', null, isCloud(v.id) ? 'Needs internet on the PC' : v.desc));
      row.append(el('span', 'avatar', label[0]), t);
      if (!isCloud(v.id)) {
        const hear = el('button', 'chipBtn');
        hear.innerHTML = icon('speaker', 16) + '<span>Hear</span>';
        hear.onclick = (e) => { e.stopPropagation(); preview(v.id, hear); };
        row.append(hear);
      }
      row.onclick = () => {
        voice = v.id;
        store.set('bf:voice', voice);
        showVoice();
        sample.pause();
        closeSheet('voice-sheet');
      };
      card.append(row);
    }
    list.append(card);
  }
}

function preview(id, btn) {
  if (sampling) sampling.querySelector('span').textContent = 'Hear';
  if (sampling === btn && !sample.paused) { sample.pause(); sampling = null; return; }
  sampling = btn;
  btn.querySelector('span').textContent = '…';
  sample.src = api('/api/voices/preview/' + id);
  sample.play().then(() => { btn.querySelector('span').textContent = 'Stop'; })
    .catch(() => { btn.querySelector('span').textContent = 'Hear'; toast('Could not play the sample.'); });
  sample.onended = () => { btn.querySelector('span').textContent = 'Hear'; sampling = null; };
}

/* ---------- start + follow a job ---------- */
$('bk-start').onclick = async () => {
  if (!book) return;
  const ids = [...$('bk-chapters').querySelectorAll('input')].filter((c) => c.checked).map((c) => Number(c.dataset.id));
  store.set('bf:rate', Number($('bk-speed').value));
  const fd = new FormData();
  fd.append('book_id', book.book_id);
  fd.append('voice', voice);
  fd.append('engine', isCloud(voice) ? 'edge' : 'kokoro');
  fd.append('speed', $('bk-speed').value);
  fd.append('output_format', format);
  fd.append('selected_chapters', JSON.stringify(ids));
  $('bk-start').disabled = true;
  try {
    const job = await getJSON('/api/compile', { method: 'POST', body: fd });
    closeSheet('book-sheet');
    store.set('bf:job', job.job_id);
    follow(job);
  } catch (e) {
    toast(`Couldn't start: ${e.message}`);
  } finally {
    $('bk-start').disabled = false;
  }
};

let ws = null, pollTimer = null;
const RING = 2 * Math.PI * 34;

function follow(job) {
  showJob(job);
  if (ws) ws.close();
  clearInterval(pollTimer);
  const done = (j) => ['completed', 'failed', 'cancelled'].includes(j.status);
  if (done(job)) return;
  try {
    ws = new WebSocket(SERVER.replace(/^http/, 'ws') + '/ws/jobs/' + job.job_id);
    ws.onmessage = (e) => { const j = JSON.parse(e.data); if (!j.error) showJob(j); };
    ws.onerror = () => poll(job.job_id);
  } catch { poll(job.job_id); }
}
function poll(id) {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const j = await getJSON('/api/jobs/' + id);
      showJob(j);
      if (['completed', 'failed', 'cancelled'].includes(j.status)) clearInterval(pollTimer);
    } catch { /* PC asleep — keep trying */ }
  }, 1500);
}

let lastStatus = null;
function showJob(j) {
  $('job-card').hidden = false;
  $('empty').hidden = true;
  const pct = j.status === 'completed' ? 100 : j.progress || 0;
  $('job-ring').style.strokeDashoffset = RING * (1 - pct / 100);
  $('job-pct').textContent = j.status === 'completed' ? '✓' : `${Math.round(pct)}%`;
  $('job-title').textContent = j.book_title || 'Audiobook';
  const prep = $('job-prep');
  prep.classList.toggle('done', j.status === 'completed');
  prep.classList.toggle('bad', j.status === 'failed' || j.status === 'cancelled');
  const actions = $('job-actions');
  actions.replaceChildren();
  const btn = (cls, label, ic, fn) => {
    const b = el('button', cls);
    b.innerHTML = (ic ? icon(ic, 16) : '') + `<span>${label}</span>`;
    b.onclick = fn;
    actions.append(b);
  };
  const dismiss = () => { store.del('bf:job'); $('job-card').hidden = true; if (ws) ws.close(); clearInterval(pollTimer); renderShelf(); };
  $('lib-dot').hidden = !['queued', 'running', 'packaging'].includes(j.status);

  if (j.status === 'queued' || j.status === 'running') {
    $('job-status').textContent = j.status === 'queued' ? 'Waiting to start…'
      : `Chapter ${Math.max(1, j.current_chapter_index)} of ${j.total_chapters}` + (j.eta_seconds > 0 ? ` · ${human(j.eta_seconds)} left` : '');
    $('job-detail').textContent = j.current_chapter_title || '';
    btn('textBtn danger', 'Stop', null, async () => {
      try { await getJSON(`/api/jobs/${j.job_id}/cancel`, { method: 'POST' }); } catch (e) { toast(e.message); }
    });
  } else if (j.status === 'packaging') {
    $('job-status').textContent = 'Putting the audiobook together…';
    $('job-detail').textContent = 'Adding chapters and cover';
  } else if (j.status === 'completed') {
    $('job-status').textContent = `Ready · made in ${human(j.elapsed_seconds)}`;
    $('job-detail').textContent = `${j.output_file} · ${(j.output_size_bytes / 1048576).toFixed(1)} MB`;
    const out = { filename: j.output_file, format: j.output_format === 'm4b' ? 'm4b' : 'zip', size_mb: +(j.output_size_bytes / 1048576).toFixed(1), duration_sec: 0 };
    if (j.output_format === 'm4b') btn('pill', 'Listen', 'play', () => { dismiss(); play(out); });
    if (saved[out.filename]) btn('pill light', 'On this phone', 'check', () => {});
    else if (saving[out.filename] != null) btn('pill light', 'Saving…', 'phone', () => {});
    else btn('pill light', 'Save to phone', 'phone', () => { saveBook(out).then(() => showJob(j)); showJob(j); });
    btn('textBtn', 'Done', null, dismiss);
    if (lastStatus && lastStatus !== 'completed') {
      toast(`“${j.book_title}” is ready.`);
      if (store.get('bf:autosave', true)) saveBook(out).then(() => showJob(j));
      loadLibrary();
    }
  } else {
    $('job-status').textContent = j.status === 'failed' ? 'Something went wrong' : 'Stopped';
    $('job-detail').textContent = j.error_message || '';
    btn('textBtn', 'Dismiss', null, dismiss);
  }
  lastStatus = j.status;
}

async function resumeJob() {
  const id = store.get('bf:job', null);
  if (!id) return;
  try { follow(await getJSON('/api/jobs/' + id)); } catch { store.del('bf:job'); }   // PC restarted — job gone
}

/* ================= PLAYER ================= */
const audio = $('audio');
const SPEEDS = [1, 1.15, 1.25, 1.5, 1.75, 2, 0.85];
let speedIdx = Math.max(0, SPEEDS.indexOf(store.get('bf:playspeed', 1)));
let now = null;   // { filename, title }

async function play(b) {
  const title = prettyTitle(b.filename);
  if (now && now.filename === b.filename) { showTab('player'); if (audio.paused) audio.play(); return; }
  /* the phone's own copy when there is one — plays with the PC off */
  let src, local = false;
  if (saved[b.filename]) {
    try { src = await localUrl(b.filename); local = true; } catch { /* lost — stream instead */ }
  }
  if (!src) src = api('/api/stream/' + encodeURIComponent(b.filename));
  now = { filename: b.filename, title };
  audio.src = src;
  audio.playbackRate = SPEEDS[speedIdx];
  const at = store.get('bf:pos:' + b.filename, 0);
  audio.addEventListener('loadedmetadata', () => {
    if (at > 5 && at < audio.duration - 10) audio.currentTime = at;
  }, { once: true });
  audio.play().catch(() => toast(local ? "Couldn't play the saved copy." : "Couldn't play — is the PC still on?"));
  $('np-sub').textContent = local ? 'From this phone' : 'Streaming from the PC';
  $('stage').replaceChildren(cover(title, 'lg'));
  $('np-title').textContent = title;
  $('mini-cover').replaceChildren(cover(title, 'xs'));
  $('mini-title').textContent = title;
  $('player-empty').hidden = true;
  $('player-body').hidden = false;
  $('btn-save-current').hidden = false;
  if ('mediaSession' in navigator) navigator.mediaSession.metadata = new MediaMetadata({ title, artist: 'BookForge', album: title });
  showTab('player');
  loadText(b.filename);
}

function stopPlayer() {
  audio.pause();
  audio.removeAttribute('src');
  now = null;
  $('player-empty').hidden = false;
  $('player-body').hidden = true;
  $('btn-save-current').hidden = true;
  book_text = null;
  setReading(false, true);
  $('btn-text').hidden = true;
  updateMini();
}

/* ================= READ ALONG =================
 * The PC records when every word is spoken (Book.m4b.words.json). Passages show as text; the word
 * being spoken lights up, and tapping any word jumps the audio there — like VOX.
 * Only the passage being read is split into word spans; the rest stay plain text (a book has
 * tens of thousands of words), and a tap there is mapped to its word from the caret position.
 */
let book_text = null;    // { file, paras, starts: Float64Array, para: Int32Array, first: Int32Array, chapters }
let reading = store.get('bf:reading', false);
let curPara = -1, curWord = -1, following = true, userTouch = 0, textRaf = 0;

async function fetchText(fn) {
  if (saved[fn] && saved[fn].hasText) {
    try {
      if (native) {
        const r = await FS.readFile({ path: `${DIR}/${fn}.words.json`, directory: 'DATA', encoding: 'utf8' });
        return JSON.parse(r.data);
      }
      const s = await idb('readonly', (st) => st.get(fn + '#text'));
      if (s) return JSON.parse(s);
    } catch { /* fall through to the PC */ }
  }
  if (!SERVER) return null;
  try {
    const res = await fetch(api('/api/transcript/' + encodeURIComponent(fn)));
    return res.ok ? await res.json() : null;
  } catch { return null; }
}

async function loadText(fn) {
  book_text = null;
  curPara = curWord = -1;
  $('btn-text').hidden = true;
  const t = await fetchText(fn);
  if (!now || now.filename !== fn) return;   // another book started meanwhile
  if (!t || !t.paras || !t.paras.length) { setReading(false, true); return; }
  const n = t.paras.reduce((s, p) => s + p.length, 0);
  const starts = new Float64Array(n), para = new Int32Array(n), first = new Int32Array(t.paras.length);
  let k = 0;
  t.paras.forEach((p, i) => { first[i] = k; for (const w of p) { starts[k] = w[1]; para[k] = i; k++; } });
  book_text = { file: fn, paras: t.paras, starts, para, first, chapters: t.chapters || [] };
  $('btn-text').hidden = false;
  renderPassages();
  setReading(reading, true);
}

function renderPassages() {
  const box = el('div', 'passages');
  box.id = 'passages';
  const heads = new Map((book_text.chapters || []).map((c) => [c.para, c.title]));
  book_text.paras.forEach((p, i) => {
    if (heads.has(i) && book_text.chapters.length > 1) box.append(el('h3', 'chapTitle', heads.get(i)));
    const node = el('p', 'passage', p.map((w) => w[0]).join(''));
    node.dataset.i = i;
    box.append(node);
  });
  box.addEventListener('click', onTextTap);
  ['touchstart', 'wheel', 'mousedown'].forEach((ev) => box.addEventListener(ev, () => { userTouch = Date.now(); }, { passive: true }));
  box.addEventListener('scroll', () => {
    if (Date.now() - userTouch < 1500 && following) { following = false; $('follow-btn').hidden = false; }
  }, { passive: true });
  const followBtn = el('button', 'followBtn');
  followBtn.id = 'follow-btn';
  followBtn.hidden = true;
  followBtn.innerHTML = icon('text', 16) + '<span>Back to the voice</span>';
  followBtn.onclick = () => { following = true; followBtn.hidden = true; scrollToWord(true); };
  book_text.box = box;
  book_text.followBtn = followBtn;
}

function setReading(on, quiet) {
  reading = !!on && !!book_text;
  if (!quiet) store.set('bf:reading', !!on);
  const page = document.querySelector('.playerPage');
  page.classList.toggle('reading', reading);
  $('btn-text').classList.toggle('on', reading);
  const stage = $('stage');
  stage.classList.toggle('text', reading);
  if (reading) {
    stage.replaceChildren(book_text.box, book_text.followBtn);
    following = true;
    book_text.followBtn.hidden = true;
    curPara = -1;
    syncText(true);
  } else if (now) {
    stage.replaceChildren(cover(now.title, 'lg'));
  }
  textLoop();
}
$('btn-text').onclick = () => setReading(!reading);

/* the word being spoken at time t (last word that started at or before t) */
function wordAt(t) {
  const s = book_text.starts;
  let lo = 0, hi = s.length - 1, ans = 0;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (s[mid] <= t) { ans = mid; lo = mid + 1; } else hi = mid - 1;
  }
  return ans;
}

function passageNode(i) { return book_text.box.querySelector(`.passage[data-i="${i}"]`); }

function splitPassage(i) {
  const node = passageNode(i);
  if (!node) return;
  const f = book_text.first[i];
  node.replaceChildren(...book_text.paras[i].map((w, j) => { const s = el('span', 'w', w[0]); s.dataset.w = f + j; return s; }));
}
function joinPassage(i) {
  const node = passageNode(i);
  if (node) node.textContent = book_text.paras[i].map((w) => w[0]).join('');
}

function syncText(jump) {
  if (!book_text || !reading) return;
  const w = wordAt(audio.currentTime + 0.05);
  const p = book_text.para[w];
  if (p !== curPara) {
    if (curPara >= 0) { const old = passageNode(curPara); if (old) old.classList.remove('now'); joinPassage(curPara); }
    curPara = p;
    splitPassage(p);
    passageNode(p).classList.add('now');
    curWord = -1;
  }
  if (w !== curWord) {
    const box = book_text.box;
    const prev = box.querySelector('.w.on');
    if (prev) prev.classList.remove('on');
    const span = box.querySelector(`.w[data-w="${w}"]`);
    if (span) span.classList.add('on');
    curWord = w;
    if (following) scrollToWord(jump);
  }
}

function scrollToWord(jump) {
  const box = book_text && book_text.box;
  const span = box && (box.querySelector('.w.on') || passageNode(curPara));
  if (!span) return;
  const b = box.getBoundingClientRect(), r = span.getBoundingClientRect();
  /* keep the spoken line in the upper third; only move when it drifts out of the middle band */
  if (jump || r.top < b.top + b.height * 0.15 || r.bottom > b.top + b.height * 0.7) {
    box.scrollTo({ top: box.scrollTop + (r.top - b.top) - b.height * 0.3, behavior: jump ? 'auto' : 'smooth' });
  }
}

function textLoop() {
  cancelAnimationFrame(textRaf);
  if (!reading || !book_text) return;
  const tick = () => {
    syncText(false);
    if (!audio.paused) textRaf = requestAnimationFrame(tick);
  };
  tick();
}
audio.addEventListener('play', textLoop);
audio.addEventListener('seeked', () => syncText(following));
audio.addEventListener('timeupdate', () => syncText(false));   // keeps up even when frames are throttled (screen off, background)

/* tap a word → the voice goes there */
function onTextTap(e) {
  let w = e.target.dataset && e.target.dataset.w;
  if (w == null) {
    const node = e.target.closest('.passage');
    if (!node) return;
    const i = Number(node.dataset.i);
    let off = 0;
    const pos = document.caretPositionFromPoint ? document.caretPositionFromPoint(e.clientX, e.clientY)
      : document.caretRangeFromPoint ? (() => { const r = document.caretRangeFromPoint(e.clientX, e.clientY); return r && { offsetNode: r.startContainer, offset: r.startOffset }; })() : null;
    if (pos && node.contains(pos.offsetNode)) off = pos.offset;
    let acc = 0, j = 0;
    const words = book_text.paras[i];
    for (; j < words.length - 1; j++) { acc += words[j][0].length; if (acc > off) break; }
    w = book_text.first[i] + j;
  }
  w = Number(w);
  const t = book_text.starts[w];
  following = true;
  if (book_text.followBtn) book_text.followBtn.hidden = true;
  audio.currentTime = Math.max(0, t - 0.02);
  if (audio.paused) audio.play();
  syncText(false);
}

function updateMini() {
  $('mini').hidden = !now || tab === 'player';
  const playing = !audio.paused;
  setIcon($('btn-play'), playing ? 'pause' : 'play');
  setIcon($('mini-btn'), playing ? 'pause' : 'play');
  $('btn-play').setAttribute('aria-label', playing ? 'Pause' : 'Play');
  $('stage').classList.toggle('live', playing);
}

const toggle = () => { if (!now) return; audio.paused ? audio.play() : audio.pause(); };
const skip = (d) => { if (now && isFinite(audio.duration)) audio.currentTime = Math.min(audio.duration, Math.max(0, audio.currentTime + d)); };
$('btn-play').onclick = toggle;
$('mini-btn').onclick = (e) => { e.stopPropagation(); toggle(); };
$('mini').onclick = () => showTab('player');
$('btn-back').onclick = () => skip(-15);
$('btn-fwd').onclick = () => skip(30);
$('btn-save-current').onclick = () => {
  if (!now) return;
  if (saved[now.filename]) { toast('Already saved on this phone.'); return; }
  const b = books.find((x) => x.filename === now.filename);
  if (b) saveBook(b);
};
$('btn-more').onclick = () => { const b = books.find((x) => x.filename === now?.filename); if (b) bookMenu(b); };
$('btn-speed').onclick = () => {
  speedIdx = (speedIdx + 1) % SPEEDS.length;
  audio.playbackRate = SPEEDS[speedIdx];
  store.set('bf:playspeed', SPEEDS[speedIdx]);
  $('speed-txt').textContent = SPEEDS[speedIdx] + '×';
};
$('speed-txt').textContent = SPEEDS[speedIdx] + '×';

let dragging = false, lastSave = 0;
$('scrubber').oninput = () => {
  dragging = true;
  if (isFinite(audio.duration)) $('t-now').textContent = clock(($('scrubber').value / 1000) * audio.duration);
};
$('scrubber').onchange = () => {
  if (isFinite(audio.duration)) audio.currentTime = ($('scrubber').value / 1000) * audio.duration;
  dragging = false;
};
audio.addEventListener('timeupdate', () => {
  const d = audio.duration, t = audio.currentTime;
  if (!isFinite(d)) return;
  if (!dragging) {
    $('scrubber').value = (t / d) * 1000;
    $('t-now').textContent = clock(t);
  }
  $('t-left').textContent = '-' + clock(d - t);
  $('mini-progress').style.width = `${(t / d) * 100}%`;
  $('mini-sub').textContent = `${audio.paused ? 'Paused' : 'Playing'} · ${clock(d - t)} left`;
  if (now && Date.now() - lastSave > 4000) { store.set('bf:pos:' + now.filename, t); lastSave = Date.now(); }
});
['play', 'pause'].forEach((ev) => audio.addEventListener(ev, () => {
  if (now) store.set('bf:pos:' + now.filename, audio.currentTime);
  updateMini();
}));
audio.addEventListener('waiting', () => $('btn-play').classList.add('waiting'));
audio.addEventListener('playing', () => $('btn-play').classList.remove('waiting'));
audio.addEventListener('ended', () => { if (now) store.del('bf:pos:' + now.filename); });

if ('mediaSession' in navigator) {
  navigator.mediaSession.setActionHandler('play', () => audio.play());
  navigator.mediaSession.setActionHandler('pause', () => audio.pause());
  navigator.mediaSession.setActionHandler('seekbackward', () => skip(-15));
  navigator.mediaSession.setActionHandler('seekforward', () => skip(30));
}

/* ================= SETTINGS ================= */
async function loadServerInfo() {
  $('server-input').value = SERVER;
  $('st-url').textContent = SERVER.replace(/^https?:\/\//, '');
  $('st-status').textContent = 'Checking…';
  $('st-status').className = '';
  try {
    const d = await getJSON('/api/network-info');
    $('st-status').textContent = 'Connected';
    $('st-status').className = 'ok';
    $('st-engine').textContent = d.gpu_available ? 'Kokoro · graphics card' : 'Kokoro · processor (slower)';
  } catch {
    $('st-status').textContent = 'Not reachable';
    $('st-status').className = 'bad';
    $('st-engine').textContent = '—';
  }
}
/* text from a QR code or the address box → "http://ip:port", or null */
function pcAddress(text) {
  let v = String(text || '').trim();
  if (!v) return null;
  if (!/^https?:\/\//i.test(v)) v = 'http://' + v;
  try {
    const u = new URL(v);
    return `${u.protocol}//${u.hostname}:${u.port || 8000}`;
  } catch { return null; }
}

/* make this PC the default — only if it really is a BookForge server */
async function connectTo(addr) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 5000);
  try {
    const res = await fetch(addr + '/api/network-info', { signal: ctl.signal });
    if (!res.ok) throw new Error();
    await res.json();
  } catch {
    toast(`No BookForge server answered at ${addr.replace(/^https?:\/\//, '')}. Is the PC on the same Wi-Fi with the server running?`);
    return false;
  } finally { clearTimeout(timer); }
  SERVER = addr;
  store.set('bf:server', addr);
  toast('Connected to your PC.');
  loadServerInfo();
  loadVoices();
  loadLibrary();
  resumeJob();
  return true;
}

$('btn-connect').onclick = () => {
  const v = pcAddress($('server-input').value);
  if (v) connectTo(v);
  else toast("That doesn't look like an address.");
};

/* ---------- QR scanner ---------- */
let scanStream = null, scanLoop = 0, scanBusy = false;
const detector = 'BarcodeDetector' in window ? new BarcodeDetector({ formats: ['qr_code'] }) : null;

function decodeImage(src) {
  /* src: video or image → text or null */
  const w = src.videoWidth || src.naturalWidth || src.width, h = src.videoHeight || src.naturalHeight || src.height;
  if (!w || !h) return null;
  const scale = Math.min(1, 800 / Math.max(w, h));
  const c = decodeImage.canvas ||= document.createElement('canvas');
  c.width = Math.round(w * scale);
  c.height = Math.round(h * scale);
  const ctx = c.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(src, 0, 0, c.width, c.height);
  const img = ctx.getImageData(0, 0, c.width, c.height);
  const hit = window.jsQR && jsQR(img.data, img.width, img.height, { inversionAttempts: 'attemptBoth' });
  return hit ? hit.data : null;
}
async function read(src) {
  if (detector) {
    try { const r = await detector.detect(src); if (r.length) return r[0].rawValue; } catch { /* fall back */ }
  }
  return decodeImage(src);
}

async function gotCode(text) {
  const addr = pcAddress(text);
  if (!addr) { toast("That QR code isn't a BookForge PC."); return false; }
  $('scan-box').classList.add('found');
  stopScan();
  closeSheet('scan-sheet');
  return connectTo(addr);
}

async function openScanner() {
  $('scan-box').classList.remove('found');
  $('scan-msg').hidden = true;
  openSheet('scan-sheet');
  const video = $('scan-video');
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    $('scan-msg').textContent = 'The camera only works in the BookForge app or on a secure page. Take a photo of the code instead.';
    $('scan-msg').hidden = false;
    return;
  }
  try {
    scanStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
  } catch (e) {
    $('scan-msg').textContent = /denied|NotAllowed/i.test(e.name + e.message)
      ? 'Camera permission was denied. Allow it in the phone settings, or use a photo of the code.'
      : 'No camera available. Use a photo of the code instead.';
    $('scan-msg').hidden = false;
    return;
  }
  if ($('scan-sheet').hidden) { stopScan(); return; }   // closed while asking for permission
  video.srcObject = scanStream;
  await video.play().catch(() => {});
  const loop = async () => {
    if (!scanStream) return;
    if (!scanBusy && video.readyState >= 2) {
      scanBusy = true;
      const text = await read(video);
      scanBusy = false;
      if (text && scanStream) { gotCode(text); return; }
    }
    scanLoop = requestAnimationFrame(loop);
  };
  loop();
}
function stopScan() {
  cancelAnimationFrame(scanLoop);
  if (scanStream) scanStream.getTracks().forEach((t) => t.stop());
  scanStream = null;
  $('scan-video').srcObject = null;
}
$('btn-scan').onclick = openScanner;
$('btn-scan-empty').onclick = openScanner;
$('scan-cancel').onclick = () => { stopScan(); closeSheet('scan-sheet'); };
$('scan-sheet').addEventListener('click', (e) => { if (e.target === $('scan-sheet')) stopScan(); });
$('scan-photo').onclick = () => $('scan-file').click();
$('scan-file').onchange = async () => {
  const f = $('scan-file').files[0];
  $('scan-file').value = '';
  if (!f) return;
  const img = new Image();
  img.src = URL.createObjectURL(f);
  const ok = await new Promise((r) => { img.onload = () => r(true); img.onerror = () => r(false); });
  if (!ok) { toast("Couldn't open that photo."); return; }
  const text = await read(img);
  URL.revokeObjectURL(img.src);
  if (text) gotCode(text);
  else toast('No QR code found in that photo. Try again closer to the screen.');
};

/* ---------- start ---------- */
paintIcons();
$('empty-art').append(cover('Your next book', 'md'));
$('player-empty-art').append(cover('Nothing playing', 'md'));
updateMini();
showStorage();
loadLibrary();
if (SERVER) { loadVoices(); resumeJob(); }
else setTimeout(openScanner, 400);   // first start in the app: no PC yet — scan its code
if ('serviceWorker' in navigator && servedByPC) navigator.serviceWorker.register('sw.js').catch(() => {});
