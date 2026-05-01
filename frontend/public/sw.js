const CACHE_NAME = 'smarttask-v1'
const STATIC_ASSETS = [
  '/',
  '/index.html',
]

// 安装：缓存核心资源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  )
  self.skipWaiting()
})

// 激活：清理旧缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  )
  self.clients.claim()
})

// 拦截请求：网络优先，失败降级缓存
self.addEventListener('fetch', (event) => {
  // API 请求不缓存，直接走网络
  if (event.request.url.includes('/api/')) {
    return
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // 成功则更新缓存
        const clone = response.clone()
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone))
        return response
      })
      .catch(() => {
        // 网络失败则从缓存读取
        return caches.match(event.request)
      })
  )
})
