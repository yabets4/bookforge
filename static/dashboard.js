/* BookForge PC dashboard: phone QR, machine status, live jobs, finished audiobooks */
const $ = (id) => document.getElementById(id);
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
function human(sec) {
  sec = Math.round(sec || 0);
  if (sec < 60) return `${sec}s`;
  const h = Math.floor(sec / 3600), m = Math.round((sec % 3600) / 60);
  return h ? `${h} h ${m} min` : `${m} min`;
}
const prettyTitle = (name) => name.replace(/\.(m4b|mp3|zip)$/i, '').replace(/_[0-9a-f]{8}$/i, '').replace(/_/g, ' ').trim();
const PALETTES = [['#c0643c', '#e8a67c'], ['#6f8462', '#b5c49d'], ['#3f5a6e', '#8fa9bb'], ['#8a4f6a', '#d2a0b5'], ['#b38a2e', '#e6cb83'], ['#4f7a74', '#9fc6bd'], ['#6b5847', '#c4ab91']];
function hash(s) { let h = 7; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }
function cover(title) {
  const [a, b] = PALETTES[hash(title) % PALETTES.length];
  const n = el('div', 'cover');
  n.style.setProperty('--c1', a);
  n.style.setProperty('--c2', b);
  return n;
}
let toastTimer;
function toast(msg) {
  $('toast').textContent = msg;
  $('toast').hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $('toast').hidden = true; }, 3500);
}
async function getJSON(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/* ---------- connect ---------- */
async function loadNetwork() {
  try {
    const d = await getJSON('/api/network-info');
    $('qr').src = d.qr_code;
    $('app-url').textContent = d.app_url;
  } catch { /* shown as offline by the status poll */ }
}
$('copy').onclick = async () => {
  try { await navigator.clipboard.writeText($('app-url').textContent); toast('Address copied.'); } catch { toast('Select the address and copy it.'); }
};

/* ---------- machine ---------- */
async function loadMachine() {
  try {
    const d = await getJSON('/api/server-info');
    $('live').className = 'live';
    $('live').querySelector('span').textContent = 'Running';
    $('m-engine').textContent = d.device === 'cuda' ? 'Kokoro · graphics card' : 'Kokoro · processor';
    $('m-engine').className = d.device === 'cuda' ? 'ok' : '';
    $('m-gpu').textContent = d.gpu_name || 'none';
    $('m-mem').textContent = d.gpu_mem_total_mb ? `${((d.gpu_mem_total_mb - d.gpu_mem_free_mb) / 1024).toFixed(1)} of ${(d.gpu_mem_total_mb / 1024).toFixed(1)} GB used` : '—';
    $('m-model').textContent = d.engine_loaded ? 'Loaded' : 'Loads with the first book';
    $('m-up').textContent = human(d.uptime_sec);
  } catch {
    $('live').className = 'live off';
    $('live').querySelector('span').textContent = 'Server stopped';
  }
}

/* ---------- jobs ---------- */
const RING = 2 * Math.PI * 34;
const openLogs = new Set();
const ACTIVE = ['queued', 'running', 'packaging'];

async function loadJobs() {
  let jobs;
  try { jobs = await getJSON('/api/jobs'); } catch { return; }
  const box = $('jobs');
  const scrolls = {};
  box.querySelectorAll('.log').forEach((l) => { scrolls[l.dataset.id] = l.scrollTop; });
  box.replaceChildren();
  $('jobs-empty').hidden = jobs.length > 0;
  const active = jobs.filter((j) => ACTIVE.includes(j.status)).length;
  $('jobs-count').textContent = jobs.length ? `${active} working · ${jobs.length} since start` : '';
  document.title = active ? `(${active}) BookForge Server` : 'BookForge Server';

  for (const j of jobs) {
    const card = el('div', 'card job' + (j.status === 'completed' ? ' done' : ['failed', 'cancelled'].includes(j.status) ? ' bad' : ''));
    const pct = j.status === 'completed' ? 100 : j.progress || 0;
    card.innerHTML = `<svg class="ring" viewBox="0 0 80 80"><circle class="track" cx="40" cy="40" r="34"/>` +
      `<circle class="fill" cx="40" cy="40" r="34" stroke-dasharray="${RING}" stroke-dashoffset="${RING * (1 - pct / 100)}"/>` +
      `<text x="40" y="45" text-anchor="middle">${j.status === 'completed' ? '✓' : Math.round(pct) + '%'}</text></svg>`;
    const body = el('div', 'jobBody');
    body.append(el('h3', null, j.book_title || 'Book'));
    let line;
    if (j.status === 'running') line = `Chapter ${Math.max(1, j.current_chapter_index)} of ${j.total_chapters} · ${j.current_chapter_title || ''}`;
    else if (j.status === 'queued') line = 'Waiting to start';
    else if (j.status === 'packaging') line = 'Putting the audiobook together';
    else if (j.status === 'completed') line = `Done in ${human(j.elapsed_seconds)} · ${j.output_file} · ${(j.output_size_bytes / 1048576).toFixed(1)} MB`;
    else if (j.status === 'failed') line = j.error_message || 'Failed';
    else line = 'Stopped';
    body.append(el('div', 'jobLine', line));

    const meta = el('div', 'jobMeta');
    const statusTag = { running: 'hot', packaging: 'hot', queued: '', completed: 'ok', failed: 'bad', cancelled: 'bad' }[j.status];
    meta.append(el('span', 'tag ' + statusTag, j.status));
    meta.append(el('span', 'tag', `${j.engine === 'kokoro' ? 'Kokoro' : 'Online'} · ${j.voice}`));
    meta.append(el('span', 'tag', `${j.speed}× · ${j.output_format === 'm4b' ? 'M4B' : 'MP3 zip'}`));
    if (ACTIVE.includes(j.status)) {
      meta.append(el('span', 'tag', `${human(j.elapsed_seconds)} so far`));
      if (j.eta_seconds > 0) meta.append(el('span', 'tag hot', `${human(j.eta_seconds)} left`));
    }
    body.append(meta);

    if (openLogs.has(j.job_id)) {
      const log = el('div', 'log', (j.logs || []).join('\n') || 'No log yet.');
      log.dataset.id = j.job_id;
      body.append(log);
      requestAnimationFrame(() => { log.scrollTop = scrolls[j.job_id] ?? log.scrollHeight; });
    }

    const btns = el('div', 'jobBtns');
    const logBtn = el('button', 'chipBtn', openLogs.has(j.job_id) ? 'Hide log' : 'Log');
    logBtn.onclick = () => { openLogs.has(j.job_id) ? openLogs.delete(j.job_id) : openLogs.add(j.job_id); loadJobs(); };
    btns.append(logBtn);
    if (ACTIVE.includes(j.status)) {
      const stop = el('button', 'chipBtn danger', 'Stop');
      stop.onclick = async () => { await fetch(`/api/jobs/${j.job_id}/cancel`, { method: 'POST' }); loadJobs(); };
      btns.append(stop);
    }
    card.append(body, btns);
    box.append(card);
  }
}

/* ---------- finished audiobooks ---------- */
async function loadLibrary() {
  let books;
  try { books = await getJSON('/api/audiobooks'); } catch { return; }
  const box = $('library');
  box.replaceChildren();
  const total = books.reduce((s, b) => s + b.size_mb, 0);
  $('lib-size').textContent = books.length ? `${books.length} · ${total.toFixed(0)} MB on this PC` : '';
  if (!books.length) { box.append(el('div', 'libEmpty', 'Nothing finished yet.')); return; }
  for (const b of books) {
    const title = prettyTitle(b.filename);
    const row = el('div', 'row');
    const text = el('div', 'rowText');
    text.append(el('b', null, title), el('span', null, [b.format.toUpperCase(), b.duration_sec ? human(b.duration_sec) : null, `${b.size_mb} MB`, new Date(b.created_at * 1000).toLocaleString()].filter(Boolean).join(' · ')));
    const open = el('a', 'chipBtn', 'Download');
    open.href = '/api/download/' + encodeURIComponent(b.filename);
    open.style.textDecoration = 'none';
    let armed = false;
    const del = el('button', 'chipBtn danger', 'Delete');
    del.onclick = async () => {
      if (!armed) { armed = true; del.textContent = 'Sure?'; setTimeout(() => { armed = false; del.textContent = 'Delete'; }, 3000); return; }
      await fetch('/api/audiobooks/' + encodeURIComponent(b.filename), { method: 'DELETE' });
      toast(`Deleted “${title}”.`);
      loadLibrary();
    };
    row.append(cover(title), text, open, del);
    box.append(row);
  }
}

/* ---------- refresh ---------- */
let lastActive = 0;
async function tick() {
  await Promise.all([loadMachine(), loadJobs()]);
  const active = document.querySelectorAll('.job:not(.done):not(.bad)').length;
  if (active !== lastActive) loadLibrary();   // a job just finished (or started)
  lastActive = active;
}
loadNetwork();
loadLibrary();
tick();
setInterval(tick, 1500);
setInterval(loadNetwork, 60000);   // the PC's Wi-Fi address can change
