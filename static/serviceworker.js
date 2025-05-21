const CACHE_NAME = 'margdata-dashboard-v3';
const urlsToCache = [
    '/donations/login/',
    '/donations/admin-dashboard/',
    '/donations/user-dashboard/',
    '/static/css/style.css',
    '/static/css/bootstrap.min.css',
    '/static/css/plugins.min.css',
    '/static/css/kaiadmin.min.css',
    '/static/css/demo.css',
    '/static/js/core/jquery-3.7.1.min.js',
    '/static/js/core/popper.min.js',
    '/static/js/core/bootstrap.min.js',
    '/static/js/kaiadmin.min.js',
    '/static/assets/img/MARGDATA__1.png',
    '/static/assets/img/margdata - copy.png',
    '/static/manifest.json',
    '/static/assets/css/fonts.min.css',
    '/static/assets/js/plugin/webfont/webfont.min.js',
    '/static/assets/js/plugin/jquery-scrollbar/jquery.scrollbar.min.js',
    '/static/assets/js/plugin/chart.js/chart.min.js',
    '/static/assets/js/plugin/jquery.sparkline/jquery.sparkline.min.js',
    '/static/assets/js/plugin/chart-circle/circles.min.js',
    '/static/assets/js/plugin/datatables/datatables.min.js',
    '/static/assets/js/plugin/bootstrap-notify/bootstrap-notify.min.js',
    '/static/assets/js/plugin/sweetalert/sweetalert.min.js',
    '/static/assets/js/kaiadmin.min.js',
    '/static/assets/js/setting-demo.js',
    '/static/assets/js/demo.js'
];

// Install a service worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
    self.skipWaiting();
});

// Cache and return requests
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return the cached response if found
                if (response) {
                    return response;
                }

                // Clone the request because it's a one-time use
                const fetchRequest = event.request.clone();

                // Make network request and cache the response
                return fetch(fetchRequest).then(
                    response => {
                        // Check if we received a valid response
                        if(!response || response.status !== 200) {
                            return response;
                        }

                        // Clone the response because it's a one-time use
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                // Cache all static assets and donation routes
                                if (event.request.url.indexOf('/static/') !== -1 || 
                                    event.request.url.indexOf('/donations/') !== -1) {
                                    cache.put(event.request, responseToCache);
                                }
                            });

                        return response;
                    }
                );
            })
    );
});

// Update a service worker
self.addEventListener('activate', event => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
}); 