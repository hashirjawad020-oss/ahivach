const CACHE_NAME = 'ahivach-cache-v2';
const URLS_TO_CACHE = [
  '/',
  '/dashboard',
  '/simulator',
  '/prevention',
  '/emergency-card',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(URLS_TO_CACHE);
    })
  );
  self.skipWaiting(); // Force the waiting service worker to become the active service worker
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  
  // Network First, falling back to cache strategy
  event.respondWith(
    fetch(event.request).then((fetchRes) => {
      return caches.open(CACHE_NAME).then((cache) => {
        cache.put(event.request, fetchRes.clone());
        return fetchRes;
      });
    }).catch(() => {
      return caches.match(event.request).then((response) => {
        return response || new Response("Offline Mode: Please check your internet connection.");
      });
    })
  );
});

self.addEventListener('activate', (event) => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (!cacheWhitelist.includes(cacheName)) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim(); // Ensure clients are immediately controlled by the new worker
});
