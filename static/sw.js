const CACHE_NAME = 'perra-cache-v1';
const urlsToCache = [
  '/',
  '/static/1000162143-fotor-bg-remover-2026030214294.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
