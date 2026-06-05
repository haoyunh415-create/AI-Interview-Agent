# syntax=docker/dockerfile:1
# ── AI 面试助手 — Frontend ──
# Multi-stage build: node build → nginx static serve
#
# Stage names are used by docker-compose.yml for the frontend-builder service.

# ── Stage 1: Builder ──
FROM node:22-alpine AS builder

WORKDIR /build

# Copy dependency manifests first (layer caching)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: Static files via nginx ──
FROM nginx:stable-alpine AS runtime

# Nginx config for SPA routing (used when running standalone without the main nginx proxy)
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
        add_header Service-Worker-Allowed /; \
    } \
    location /sw.js { \
        add_header Cache-Control "no-cache"; \
        add_header Service-Worker-Allowed /; \
        proxy_cache_bypass $http_pragma; \
    } \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
    gzip on; \
    gzip_types text/plain text/css application/json application/javascript image/svg+xml; \
    gzip_min_length 1000; \
}' > /etc/nginx/conf.d/default.conf

# Copy built static files from builder
COPY --from=builder /build/out /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
