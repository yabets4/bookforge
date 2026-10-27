// BookForge service worker — network first, so a new UI shows up right away; cache only for offline
const CACHE_NAME = 'bookforge-v2';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET' || e.request.url.includes('/api/')) return;
  e.respondWith(
    fetch(e.request)
      .then((res) => { const copy = res.clone(); caches.open(CACHE_NAME).then((c) => c.put(e.request, copy)); return res; })
      .catch(() => caches.match(e.request))
  );
});
