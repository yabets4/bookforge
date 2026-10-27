// The phone app moved to /app/ (its worker is /app/sw.js). This retires the old worker on phones that still have it.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k)))).then(() => self.registration.unregister()));
});
