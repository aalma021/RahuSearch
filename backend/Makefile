# ------------------------------------------
# MAKEFILE (STRICT ORDER + HEALTH CHECK)
# ------------------------------------------

ENV_NAME := $(shell grep "^name:" environment.yml | sed 's/name: //')
CUR_PATH := $(CURDIR)

.PHONY: all env up api wait_backend frontend logs stop reset stop_background_services wait_frontend

# ------------------------------------------
# DEFAULT FLOW
# ------------------------------------------
all: stop_background_services env up api wait_backend frontend wait_frontend piggy

# ------------------------------------------
# KILL OLD SERVICES
# ------------------------------------------
stop_background_services:
	@echo ">>> Cleaning previously running services..."

	@echo ">>> Killing frontend (port 3000)..."
	@FRPID=$$(lsof -ti :3000); \
	if [ -n "$$FRPID" ]; then \
		kill -9 $$FRPID || true; \
		echo "Frontend killed: $$FRPID"; \
	else \
		echo "No frontend running."; \
	fi

	@echo ">>> Killing backend (port 8000)..."
	@BEPID=$$(lsof -ti :8000); \
	if [ -n "$$BEPID" ]; then \
		kill -9 $$BEPID || true; \
		echo "Backend killed: $$BEPID"; \
	else \
		echo "No backend running."; \
	fi

	rm -f backend.pid frontend.pid backend.log frontend.log
	@echo "✔ Old services cleaned ✓"

# ------------------------------------------
# CONDA ENV
# ------------------------------------------
env:
	@echo ">>> Checking Conda environment: $(ENV_NAME)"
	@if conda env list | grep -q "^$(ENV_NAME) "; then \
		echo ">>> Environment exists."; \
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

	@echo ">>> Waiting for OpenSearch to be ready..."
	@bash -c '\
	for i in {1..60}; do \
		if curl -s http://localhost:9200 >/dev/null; then \
			echo ">>> OpenSearch is ready ✓"; exit 0; \
		fi; \
		echo "Waiting for OpenSearch... ($$i/60)"; \
		sleep 2; \
	done; \
	echo ">>> ERROR: OpenSearch did not start"; exit 1; \
	'

# ------------------------------------------
# BACKEND
# ------------------------------------------
api:
	@echo ">>> Starting Backend API..."
	@bash -c '\
		source $$(conda info --base)/etc/profile.d/conda.sh && \
		conda activate $(ENV_NAME) && \
		nohup python -u -m app.main > backend.log 2>&1 & \
		echo $$! > backend.pid \
	'
	@echo ">>> Backend process started"


# ------------------------------------------
# WAIT UNTIL BACKEND IS REALLY UP
# ------------------------------------------
wait_backend:
	@echo ">>> Waiting for Backend health check..."
	@bash -c '\
	for i in {1..60}; do \
		if curl -s http://localhost:8000/health >/dev/null; then \
			echo ">>> Backend is healthy ✓"; exit 0; \
		fi; \
		echo "Waiting for Backend... ($$i/60)"; \
		sleep 2; \
	done; \
	echo ">>> ERROR: Backend did not become healthy"; \
	echo ">>> Check backend.log"; exit 1; \
	'
	
# ------------------------------------------
# FRONTEND (NODE 24 + VITE + AUTO BROWSER)
# ------------------------------------------
frontend:
	@echo ">>> Starting Frontend (Vite, Node 24)..."

	@bash -c '\
		set -e; \
		cd ../frontend; \
		if [ ! -f .nvmrc ]; then \
			echo "❌ .nvmrc not found in frontend/"; exit 1; \
		fi; \
		if [ ! -s $$HOME/.nvm/nvm.sh ]; then \
			echo "❌ nvm not found. Install nvm first."; exit 1; \
		fi; \
		source $$HOME/.nvm/nvm.sh; \
		nvm use; \
		NODE_MAJOR=$$(node -v | sed "s/v//" | cut -d. -f1); \
		if [ $$NODE_MAJOR -lt 24 ]; then \
			echo "❌ Unsupported Node version: $$(node -v). Required: >=24"; exit 1; \
		fi; \
		if [ ! -f package-lock.json ]; then \
			echo "⚠️ package-lock.json not found → cleaning node_modules & npm cache"; \
			rm -rf node_modules; \
			npm cache clean --force; \
		else \
			echo "✔ package-lock.json found → preserving node_modules resolution"; \
		fi; \
		echo ">>> Running npm install"; \
		npm install; \
		echo ">>> Starting Vite dev server (background)"; \
		nohup npm run dev > $(CUR_PATH)/frontend.log 2>&1 & \
		echo $$! > $(CUR_PATH)/frontend.pid; \
	'

	@echo ">>> Frontend process started ✓ (background)"

# ------------------------------------------
# WAIT UNTIL FRONTEND IS REALLY UP
# ------------------------------------------
wait_frontend:
	@echo ">>> Waiting for Frontend to be ready..."
	@bash -c '\
	for i in {1..60}; do \
		if curl -s http://localhost:3000 >/dev/null; then \
			echo ">>> Frontend is ready ✓"; exit 0; \
		fi; \
		echo "Waiting for Frontend... ($$i/60)"; \
		sleep 2; \
	done; \
	echo ">>> ERROR: Frontend did not become ready"; \
	echo ">>> Check frontend.log"; exit 1; \
	'

# ------------------------------------------
# LOGS
# ------------------------------------------
logs:
	@echo ">>> Streaming backend logs..."
	@tail -f backend.log

# ------------------------------------------
# STOP EVERYTHING
# ------------------------------------------
stop:
	@echo ">>> Stopping docker services..."
	docker compose down
	@echo ">>> Use 'make all' to restart."

# ------------------------------------------
# FULL RESET
# ------------------------------------------
reset:
	@echo ">>> FULL RESET"
	docker compose down -v
	rm -f backend.pid frontend.pid backend.log frontend.log
	@echo ">>> Clean slate. Run 'make all'."

# ------------------------------------------
# PINGGY (FRONTEND PUBLIC TUNNEL)
# ------------------------------------------
piggy:
	@echo ">>> Starting Pinggy tunnel for FRONTEND (port 3000)..."
	@echo ">>> Public URL will be printed below"
	@echo ">>> Press CTRL+C to stop the tunnel"
	@ssh -p 443 -R 80:localhost:3000 a.pinggy.io | tee piggy.log