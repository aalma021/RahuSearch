# ------------------------------------------
# MAKEFILE (BACKEND & FRONTEND SEPARATE DEPLOY)
# ------------------------------------------

ENV_NAME := $(shell grep "^name:" environment.yml | sed 's/name: //')
CUR_PATH := $(CURDIR)

.PHONY: \
	env up \
	backend backend_wait backend_deploy backend_piggy \
	frontend frontend_wait frontend_deploy frontend_piggy \
	logs stop reset clean

# ------------------------------------------
# CLEAN OLD PROCESSES
# ------------------------------------------
clean:
	@echo ">>> Cleaning old processes..."

	@FRPID=$$(lsof -ti :3000); \
	if [ -n "$$FRPID" ]; then kill -9 $$FRPID || true; fi

	@BEPID=$$(lsof -ti :8000); \
	if [ -n "$$BEPID" ]; then kill -9 $$BEPID || true; fi

	rm -f backend.pid frontend.pid backend.log frontend.log piggy-backend.log piggy-frontend.log
	@echo "✔ Cleaned"

# ------------------------------------------
# CONDA ENV
# ------------------------------------------
env:
	@echo ">>> Checking Conda environment: $(ENV_NAME)"
	@if conda env list | grep -q "^$(ENV_NAME) "; then \
		echo "✔ Environment exists"; \
	else \
		echo ">>> Creating environment..."; \
		conda env create -f environment.yml; \
	fi

# ------------------------------------------
# OPENSEARCH
# ------------------------------------------
up:
	@echo ">>> Starting OpenSearch..."
	docker compose up -d opensearch

# ------------------------------------------
# BACKEND LOCAL START
# ------------------------------------------
backend: env up
	@echo ">>> Starting Backend API (local)..."
	@bash -c '\
		source $$(conda info --base)/etc/profile.d/conda.sh && \
		conda activate $(ENV_NAME) && \
		nohup python -u -m app.main > backend.log 2>&1 & \
		echo $$! > backend.pid \
	'
	@echo "✔ Backend started (background)"

# ------------------------------------------
# BACKEND HEALTH CHECK
# ------------------------------------------
backend_wait:
	@echo ">>> Waiting for Backend health..."
	@bash -c '\
	for i in {1..60}; do \
		if curl -s http://localhost:8000/health >/dev/null; then \
			echo "✔ Backend healthy"; exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "❌ Backend not healthy"; exit 1; \
	'

# ------------------------------------------
# BACKEND DEPLOY (LOCAL + PINGGY)
# ------------------------------------------
backend_deploy: clean backend backend_wait
	@echo ""
	@echo "=============================================="
	@echo "🚀 BACKEND IS READY"
	@echo "👉 Opening PUBLIC tunnel via Pinggy"
	@echo "👉 COPY the URL below and put it into frontend config"
	@echo "=============================================="
	@echo ""
	@ssh -p 443 -R 80:localhost:8000 a.pinggy.io | tee piggy-backend.log

# ------------------------------------------
# FRONTEND BUILD + PREVIEW (PROD-LIKE)
# ------------------------------------------
frontend:
	@echo ">>> Building Frontend..."
	@bash -c '\
		cd ../frontend && \
		source $$HOME/.nvm/nvm.sh && \
		nvm use && \
		npm install && \
		npm run build \
	'

	@echo ">>> Starting Frontend Preview (prod-like)..."
	@bash -c '\
		cd ../frontend && \
		nohup npx vite preview --host 0.0.0.0 --port 4173 > $(CUR_PATH)/frontend.log 2>&1 & \
		echo $$! > $(CUR_PATH)/frontend.pid \
	'

	@echo "✔ Frontend preview started (background)"

# ------------------------------------------
# FRONTEND HEALTH CHECK
# ------------------------------------------
frontend_wait:
	@echo ">>> Waiting for Frontend (preview)..."
	@bash -c '\
	for i in {1..60}; do \
		if curl -s http://localhost:4173 >/dev/null; then \
			echo "✔ Frontend preview ready"; exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "❌ Frontend preview not ready"; exit 1; \
	'

# ------------------------------------------
# FRONTEND DEPLOY (LOCAL PREVIEW)
# ------------------------------------------
frontend_deploy: frontend frontend_wait
	@echo ""
	@echo "=============================================="
	@echo "🚀 FRONTEND IS READY (PREVIEW MODE)"
	@echo "👉 Running on http://localhost:4173"
	@echo "👉 Suitable for Pinggy / Public demo"
	@echo "=============================================="
	@echo ""


# ------------------------------------------
# FRONTEND PUBLIC TUNNEL (PINGGY)
# ------------------------------------------
frontend_piggy:
	@echo ">>> Opening PUBLIC tunnel for FRONTEND (4173)"
	@ssh -p 443 -R 80:localhost:4173 a.pinggy.io | tee piggy-frontend.log

# ------------------------------------------
# LOGS
# ------------------------------------------
logs:
	@tail -f backend.log

# ------------------------------------------
# STOP EVERYTHING
# ------------------------------------------
stop:
	@echo ">>> Stopping everything..."
	docker compose down
	@make clean

# ------------------------------------------
# FULL RESET
# ------------------------------------------
reset: stop
	@docker compose down -v
	@echo "✔ Full reset done"
