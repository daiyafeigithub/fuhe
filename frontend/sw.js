// 精致饮片复核系统 Service Worker
// 用于支持PWA功能和缓存管理

const CACHE_NAME = 'fuhe-app-v1';
const urlsToCache = [
  '/frontend/',
  '/frontend/index.html',
];

self.addEventListener('install', function(event) {
  // 安装阶段：缓存应用所需的资源
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  // 拦截网络请求，优先从缓存返回
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // 如果在缓存中找到，则返回它
        if (response) {
          return response;
        }

        // 如果缓存中没有，发起网络请求
        return fetch(event.request);
      }
    )
  );
});

self.addEventListener('activate', function(event) {
  // 激活阶段：清理旧版本缓存
  var cacheWhitelist = [CACHE_NAME];

  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});