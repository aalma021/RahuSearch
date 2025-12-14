# ------------------------------------------
# MAKEFILE (STRICT ORDER + HEALTH CHECK)
# ------------------------------------------

ENV_NAME := $(shell grep "^name:" environment.yml | sed 's/name: //')
CUR_PATH := $(CURDIR)

.PHONY: all env up api wait_backend frontend logs stop reset stop_background_services

# ------------------------------------------
# DEFAULT FLOW
# ------------------------------------------
all: stop_background_services env up api wait_backend frontend

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
	@nohup conda run -n $(ENV_NAME) python -u -m app.main \
		> backend.log 2>&1 & \
	echo $$! > backend.pid
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
# FRONTEND (LAST STEP)
# ------------------------------------------
frontend:
	@echo ">>> Starting Frontend (npm start)..."
	@bash -c '\
		cd ../frontend && \
		npm install && \
		nohup npm start > $(CUR_PATH)/frontend.log 2>&1 & \
		echo $$! > $(CUR_PATH)/frontend.pid \
	'
	@echo ">>> Frontend started ✓"

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
