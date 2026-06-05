# ── Tech Chat — 统一命令入口 ──
# 使用:  make <target>
# 帮助:  make help

.PHONY: help dev backend frontend test test-python test-frontend test-e2e lint build clean install install-python install-frontend backup coverage format type-check \
        check pre-commit watch-backend watch-frontend shell db-shell deps lint-fix docker-up docker-down docker-logs docker-build deploy-check

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── 开发服务器 ──

dev: ## 同时启动前后端开发服务器
	@echo "==> 启动后端 (FastAPI :8765) + 前端 (Next.js :3000)"
	@$(MAKE) backend &
	@sleep 2
	@$(MAKE) frontend

backend: ## 启动后端开发服务器（自动重载）
	@echo "==> 启动 FastAPI :8765 (reload)"
	@uvicorn backend.main:app --host 0.0.0.0 --port 8765 --reload

frontend: ## 启动前端开发服务器
	@echo "==> 启动 Next.js :3000"
	@cd frontend && npm run dev

watch-backend: ## 后端 watch 模式（同 backend）
	@$(MAKE) backend

watch-frontend: ## 前端 watch 模式
	@echo "==> Vitest watch"
	@cd frontend && npm run test:watch

# ── 测试 ──

test: test-python test-frontend ## 运行全部测试

test-python: ## 运行 Python 测试
	@echo "==> Python 测试"
	@cd $(CURDIR) && python -m pytest tests/ -v --tb=short

test-frontend: ## 运行前端 Vitest
	@echo "==> 前端 Vitest"
	@cd frontend && npm test

test-e2e: ## 运行 E2E 测试（需要先启动前后端）
	@echo "==> Playwright E2E 测试"
	@cd frontend && npm run test:e2e

coverage: ## 运行测试并生成覆盖率报告
	@echo "==> 测试 + 覆盖率"
	@cd $(CURDIR) && python -m pytest tests/ --cov=agents --cov=backend --cov=core --cov=db --cov=report --cov-report=term-missing --cov-report=html
	@echo "覆盖率报告: htmlcov/index.html"

# ── 代码质量 ──

lint: ## 运行 ruff 检查
	@echo "==> Ruff lint"
	@cd $(CURDIR) && python -m ruff check .

lint-fix: ## 自动修复 ruff 问题
	@echo "==> Ruff auto-fix"
	@cd $(CURDIR) && python -m ruff check --fix .

type-check: ## TypeScript 类型检查
	@echo "==> TypeScript --noEmit"
	@cd frontend && npx tsc --noEmit

format: ## 格式化代码（Python + TypeScript）
	@echo "==> Ruff format"
	@cd $(CURDIR) && python -m ruff format .
	@echo "==> Prettier (TSX/JSON/CSS)"
	@cd frontend && npx prettier --write "src/**/*.{ts,tsx,json,css}"

# ════════════════════════════════════════════════════════
# Parallel checks — run lint + type-check + test concurrently
# ════════════════════════════════════════════════════════

check: ## 完整检查：lint + type-check + test（并行）
	@echo "==> 并行执行 lint + type-check + test"
	@trap 'exit 1' INT; \
	EXIT=0; \
	$(MAKE) --no-print-directory lint & PID1=$$!; \
	$(MAKE) --no-print-directory type-check & PID2=$$!; \
	$(MAKE) --no-print-directory test-python & PID3=$$!; \
	wait $$PID1; [ $$? -eq 0 ] || EXIT=1; \
	wait $$PID2; [ $$? -eq 0 ] || EXIT=1; \
	wait $$PID3; [ $$? -eq 0 ] || EXIT=1; \
	if [ $$EXIT -ne 0 ]; then echo "==> ❌ 检查未通过"; exit 1; fi; \
	echo "==> ✅ 全部检查通过"

pre-commit: ## 提交前检查：lint + type-check + test（串行，推荐 CI）
	@echo "==> 预提交检查"
	@$(MAKE) --no-print-directory lint
	@$(MAKE) --no-print-directory type-check
	@$(MAKE) --no-print-directory test-python
	@$(MAKE) --no-print-directory test-frontend
	@echo "==> ✅ 预提交检查通过"

# ── 构建 ──

build: ## 构建前端（静态导出）
	@cd frontend && npm run build

# ── 安装 ──

install: install-python install-frontend ## 安装全部依赖

install-python: ## 安装 Python 依赖
	@echo "==> Python 依赖"
	@pip install -r requirements.txt

install-python-postgres: ## 安装 Python 依赖（含 PostgreSQL 支持）
	@echo "==> Python 依赖（含 PostgreSQL）"
	@pip install -r requirements.txt psycopg2-binary

install-frontend: ## 安装前端依赖
	@echo "==> 前端依赖"
	@cd frontend && npm install

deps: ## 显示依赖版本
	@echo "==> Python"
	@python --version 2>&1
	@pip freeze 2>/dev/null | grep -iE "fastapi|uvicorn|langchain|pydantic|bcrypt|slowapi"
	@echo ""
	@echo "==> Node.js"
	@node --version 2>&1
	@cd frontend && node -e "const p=require('./package.json'); console.log('Next.js '+p.dependencies.next); console.log('React '+p.dependencies.react); console.log('Zustand '+p.dependencies.zustand);"

# ── Shell ──

shell: ## 启动 Python shell（ipython 优先）
	@echo "==> 启动 Python shell"
	@python -c "import IPython" 2>/dev/null && IPython --no-confirm-exit || python -c "import code; code.interact()"

db-shell: ## 连接 SQLite 数据库
	@echo "==> SQLite: data/interview.db"
	@sqlite3 data/interview.db

# ── Docker ──

docker-up: ## 启动 Docker 服务
	@docker compose up -d

docker-down: ## 停止 Docker 服务
	@docker compose down

docker-logs: ## 查看 Docker 日志
	@docker compose logs -f

docker-build: ## 重新构建 Docker 镜像
	@docker compose build --no-cache

# ── 数据库 ──

backup: ## 备份 SQLite 数据库
	@echo "==> 数据库备份"
	@mkdir -p backups
	@sqlite3 data/interview.db ".backup 'backups/interview_$$(date +%Y%m%d_%H%M%S).db'"
	@echo "备份完成: backups/"

# ── 数据库迁移 (Alembic) ──

db-migrate: ## 执行所有待执行的数据库迁移
	@echo "==> 执行数据库迁移"
	@cd $(CURDIR) && alembic upgrade head

db-rollback: ## 回滚最后一次数据库迁移
	@echo "==> 回滚迁移"
	@cd $(CURDIR) && alembic downgrade -1

db-history: ## 查看迁移历史
	@echo "==> 迁移历史"
	@cd $(CURDIR) && alembic history

db-check: ## 检查迁移状态
	@echo "==> 迁移状态"
	@cd $(CURDIR) && alembic current

db-revision: ## 创建新的迁移（手动编写 SQL）
	@echo "==> 创建新迁移"
	@cd $(CURDIR) && alembic revision -m "$$(read -p '请输入迁移名称: ' name; echo $$name)"

db-stamp: ## 标记当前数据库版本为最新（不执行迁移）
	@echo "==> 标记版本"
	@cd $(CURDIR) && alembic stamp head

# ── 清理 ──

clean: ## 清理临时文件
	@rm -rf frontend/.next frontend/out frontend/test-results frontend/playwright-report
	@rm -rf .pytest_cache .ruff_cache __pycache__
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov .coverage
	@echo "==> 清理完成"

# ── E2E 测试 (Playwright) ──

e2e: ## 运行 E2E 测试（自动启动前后端）
	@echo "==> Playwright E2E 测试"
	@cd frontend && npm run test:e2e

e2e-ui: ## 运行 E2E 测试（UI 模式）
	@echo "==> Playwright E2E UI 模式"
	@cd frontend && npm run test:e2e:ui

e2e-install: ## 安装 Playwright 浏览器
	@echo "==> 安装 Playwright 浏览器"
	@cd frontend && npx playwright install chromium

e2e-codegen: ## 录制 E2E 测试
	@echo "==> Playwright codegen"
	@cd frontend && npx playwright codegen http://localhost:3000

# ── 部署 ──

deploy-check: ## 生产部署前检查
	@echo "==> 部署前检查"
	@cd $(CURDIR) && python -m pytest tests/ -q --tb=short
	@cd frontend && npm test
	@cd frontend && npx tsc --noEmit
	@$(MAKE) build
	@echo "==> ✅ 部署前检查通过"
