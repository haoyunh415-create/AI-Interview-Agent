# 🚀 生产部署指南

> 从 `git clone` 到生产可用的完整流程

---

## 目录

1. [前置要求](#1-前置要求)
2. [快速启动（开发）](#2-快速启动开发)
3. [Docker 部署](#3-docker-部署)
4. [生产部署 Checklist](#4-生产部署-checklist)
5. [环境变量参考](#5-环境变量参考)
6. [数据库备份](#6-数据库备份)
7. [监控与运维](#7-监控与运维)
8. [安全加固](#8-安全加固)
9. [故障排查](#9-故障排查)

---

## 1. 前置要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | ≥ 3.11 | 运行时 |
| Node.js | ≥ 20 | 前端构建 |
| LLM API Key | — | DeepSeek / OpenAI / Anthropic |
| Docker (可选) | ≥ 24.0 | 容器化部署 |
| Nginx (可选) | ≥ 1.24 | 反向代理 + HTTPS |

---

## 2. 快速启动（开发）

```bash
# 1. 克隆项目
git clone <repo-url> tech-chat
cd tech-chat

# 2. 后端
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY
uvicorn backend.main:app --host 0.0.0.0 --port 8765 --reload

# 3. 前端（另一个终端）
cd frontend
npm install
npm run dev        # → http://localhost:3000
```

---

## 3. Docker 部署

```bash
# 构建并启动所有服务
docker compose up -d

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止
docker compose down

# 更新
git pull
docker compose build --no-cache backend
docker compose up -d
```

| 服务 | 内部端口 | 外部端口 |
|------|---------|---------|
| 前端 (Nginx) | 80 | **3000** |
| 后端 (FastAPI) | 8765 | 8765 |

---

## 4. 生产部署 Checklist

### □ 4.1 域名与 DNS

```bash
# 解析域名到服务器
your-domain.com  →  A record → <服务器 IP>
```

### □ 4.2 HTTPS（推荐 Nginx + Let's Encrypt）

```nginx
# /etc/nginx/sites-available/tech-chat
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 必需
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

```bash
# 申请证书
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 启用站点
sudo ln -s /etc/nginx/sites-available/tech-chat /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### □ 4.3 环境变量配置

```bash
# 创建生产环境配置
cp .env.example .env.production
```

**必须设置的变量：**

```env
# LLM API 密钥（至少一个）
DEEPSEEK_API_KEY=sk-your-real-key
# 或 OPENAI_API_KEY=sk-...
# 或 ANTHROPIC_API_KEY=sk-ant-...

# JWT 密钥 — 生成一个强随机字符串
# 方法: openssl rand -hex 64
JWT_SECRET=<64-字符随机十六进制字符串>

# 日志
LOG_LEVEL=INFO
LOG_FORMAT=json       # 生产推荐 JSON 格式

# 限速
RATE_LIMIT_DEFAULT=60/minute
RATE_LIMIT_AUTH=5/minute
RATE_LIMIT_LLM=10/minute

# CORS（生产环境限制来源）
ALLOWED_ORIGINS=https://your-domain.com
```

### □ 4.4 数据库初始化

```bash
# 首次启动会自动创建 SQLite 数据库
# 默认路径: ./data/interview.db
# 生产建议将 DATA_DIR 映射到持久化 volume

# 验证数据库
python -c "
from db.database import init_db
init_db()
print('Database ready')
"
```

### □ 4.5 启动服务

**方式 A：Docker**

```bash
docker compose up -d
```

**方式 B：手动启动（supervisor/systemd）**

```bash
# 后端 (FastAPI)
uvicorn backend.main:app --host 127.0.0.1 --port 8765 --workers 1

# 前端 (Next.js)
cd frontend
npx next start --port 3000
```

建议使用 `supervisor` 或 `systemd` 管理进程自启：

```ini
# /etc/systemd/system/tech-chat-backend.service
[Unit]
Description=Tech Chat Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/tech-chat
ExecStart=/opt/tech-chat/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8765
Restart=always
RestartSec=5
Environment=DATA_DIR=/opt/tech-chat/data
Environment=DEEPSEEK_API_KEY=sk-...
Environment=JWT_SECRET=...

[Install]
WantedBy=multi-user.target
```

### □ 4.6 验证部署

```bash
# 健康检查
curl https://your-domain.com/api/health
# → {"status":"ok","version":"2.2.0","active_sessions":0}

# 前端可访问
curl -I https://your-domain.com/
# → 200 OK
```

---

## 5. 环境变量参考

| 变量 | 默认值 | 生产建议 | 说明 |
|------|--------|---------|------|
| `LLM_PROVIDER` | `deepseek` | — | LLM 供应商 |
| `DEEPSEEK_API_KEY` | — | **必填** | DeepSeek 密钥 |
| `LLM_CACHE_TTL` | `300` | `300` | LLM 缓存秒数 |
| `LOG_LEVEL` | `INFO` | `INFO` | 日志级别 |
| `LOG_FORMAT` | `text` | `json` | 日志格式 |
| `JWT_SECRET` | 自动生成 | **强随机 64 字符** | JWT 签名密钥 |
| `JWT_EXPIRY_HOURS` | `72` | `24` | Token 过期时间 |
| `RATE_LIMIT_LLM` | `10/minute` | `10/minute` | LLM 接口限速 |
| `ALLOWED_ORIGINS` | `localhost` | 你的域名 | CORS |
| `DATA_DIR` | `./data` | 持久化路径 | 数据目录 |

---

## 6. 数据库备份

SQLite 数据库位于 `$DATA_DIR/interview.db`。

### 手动备份

```bash
#!/bin/bash
# backup.sh — 每天执行
BACKUP_DIR=/backups/tech-chat
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

sqlite3 /path/to/data/interview.db ".backup '$BACKUP_DIR/interview_$DATE.db'"
gzip $BACKUP_DIR/interview_$DATE.db

# 保留最近 30 天
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### 定时任务（crontab）

```cron
0 3 * * * /opt/tech-chat/scripts/backup.sh
```

### 数据恢复

```bash
sqlite3 /path/to/data/interview.db ".restore '/backups/interview_20260101_030000.db'"
```

---

## 7. 监控与运维

### 健康检查端点

```
GET /api/health
```

返回示例：
```json
{
  "status": "ok",
  "version": "2.2.0",
  "active_sessions": 3
}
```

### 日志结构（JSON 格式）

```json
{"ts": "2026-06-02T20:00:00", "level": "INFO", "logger": "tech-chat.api",
 "message": "POST /api/interview/start → 200 (4123ms)", "module": "main", "line": 56}

{"ts": "2026-06-02T20:00:05", "level": "WARNING", "logger": "tech-chat.db",
 "message": "memory persist failed (non-critical)", "module": "orchestrator", "line": 356}
```

### 监控建议

| 工具 | 用途 |
|------|------|
| **Prometheus + Grafana** | 指标聚合与仪表盘 |
| **Loki / ELK** | 日志聚合 |
| **Uptime Kuma** | 外部健康检查 |
| **Sentry** | 错误追踪 |

关键告警指标：
- LLM API 错误率 > 5%
- API 响应时间 p95 > 10s
- 活跃会话数异常增长
- 磁盘使用率 > 80%

---

## 8. 安全加固

- [ ] **JWT_SECRET** 设为 64 字符以上的强随机字符串（`openssl rand -hex 64`）
- [ ] **HTTPS** 配置 Let's Encrypt，禁用 TLS 1.0/1.1
- [ ] **CORS** 限制为具体域名，不要用 `*`
- [ ] **API 密钥** 不要提交到 git 仓库（`.env` 已在 `.gitignore` 中）
- [ ] **速率限制** 保持默认值，避免恶意耗尽 LLM 额度
- [ ] **定期备份** SQLite 数据库到独立存储
- [ ] **操作系统** 保持更新，使用非 root 用户运行服务
- [ ] **防火墙** 只开放 80/443 端口
- [ ] **Fail2ban** 对登录接口配置暴力破解防护

---

## 9. 故障排查

### 后端无法启动

```bash
# 检查 Python 版本
python --version   # 需要 ≥ 3.11

# 检查依赖
pip install -r requirements.txt --force-reinstall

# 检查端口占用
lsof -i :8765

# 查看详细日志
LOG_LEVEL=DEBUG uvicorn backend.main:app --host 0.0.0.0 --port 8765
```

### 前端无法连接后端

```bash
# 验证后端运行
curl http://localhost:8765/api/health

# 检查前端 .env 中的 API URL
# 默认: NEXT_PUBLIC_API_URL=http://localhost:8765/api
```

### 数据库损坏

```bash
# 完整性检查
sqlite3 data/interview.db "PRAGMA integrity_check;"

# 从备份恢复
sqlite3 data/interview.db ".restore '/backups/interview_20260101.db'"
```

### LLM API 错误

```bash
# 检查 API 密钥是否配置
grep API_KEY .env

# 检查网络连通性
curl -I https://api.deepseek.com

# 检查限速是否触发（响应头 X-RateLimit-Remaining）
```
