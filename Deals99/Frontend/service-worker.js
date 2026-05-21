const CACHE_VERSION = 'v1::deals99';
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/global.css',
  '/script.js',
  '/api.js',
  '/manifest.webmanifest'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter(k => k !== CACHE_VERSION).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API requests — network first
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then(res => {
          const clone = res.clone();
          caches.open(CACHE_VERSION).then(cache => cache.put(request, clone));
          return res;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // Static assets — cache first
  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request).then((res) => {
      // Populate cache for future
      const resClone = res.clone();
      caches.open(CACHE_VERSION).then(cache => cache.put(request, resClone));
      return res;
    })).catch(() => {
      // Fallback for navigation requests — serve index.html
      if (request.mode === 'navigate') return caches.match('/index.html');
      return new Response('', { status: 404 });
    })
  );
});

// Optional: message handling (skipWaiting)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});