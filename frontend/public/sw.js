/* ── AI 面试助手 — Service Worker ──
   Version: 2.1.0
   开发期间不缓存任何 JS/CSS 文件，避免缓存污染导致旧代码运行。
   生产环境只缓存静态资源，API 调用永远走网络。
*/

const CACHE = "tech-chat-static-v3";

// 安装: 跳过等待，立即激活
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

// 激活: 删除所有旧缓存，接管所有客户端
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
      );
    }).then(() => self.clients.claim())
  );
});

// 获取: 尽可能走网络
self.addEventListener("fetch", (event) => {
  const { request } = event;

  // 只处理 GET
  if (request.method !== "GET") return;

  // API 请求 — 永远不缓存
  if (request.url.includes("/api/")) return;

  // 开发模式 — 永远走网络（不缓存）
  if (self.location.hostname === "localhost" || self.location.hostname === "127.0.0.1") {
    return;
  }

  // 生产环境 — 只缓存静态资源（图片、字体、图标）
  if (/\.(png|jpg|jpeg|gif|ico|webp|svg|woff2?|ttf|eot)$/i.test(request.url)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        return cached || fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // 所有 JS/CSS/HTML — 走网络
  event.respondWith(fetch(request).catch(() => caches.match(request)));
});
