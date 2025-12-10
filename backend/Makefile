# ------------------------------------------
# MAKEFILE (PID-BASED CLEAN MANAGEMENT)
# ------------------------------------------

ENV_NAME := $(shell grep "^name:" environment.yml | sed 's/name: //')
CUR_PATH := $(CURDIR)

.PHONY: all env up frontend api logs stop reset stop_background_services

# ------------------------------------------
# DEFAULT FLOW
# ------------------------------------------
all: stop_background_services env up frontend api logs

# ------------------------------------------
# KILL OLD SERVICES USING PID FILES
# ------------------------------------------
stop_background_services:
	@echo ">>> Cleaning previously running services..."

	@echo ">>> Killing frontend..."
	@FRPID=$$(lsof -ti :3000); \
	if [ ! -z "$$FRPID" ]; then \
		kill -9 $$FRPID || true; \
		echo "Frontend killed: $$FRPID"; \
	else \
		echo "No frontend found."; \
	fi

	@echo ">>> Killing backend..."
	@BEPID=$$(lsof -ti :8000); \
	if [ ! -z "$$BEPID" ]; then \
		kill -9 $$BEPID || true; \
		echo "Backend killed: $$BEPID"; \
	else \
		echo "No backend found."; \
	fi

	rm -f $(CUR_PATH)/frontend.pid $(CUR_PATH)/backend.pid backend.log frontend.log

	@echo "✔ Previous services fully terminated ✓"

# ------------------------------------------
# CREATE ENVIRONMENT IF NOT EXISTS
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
# START OPENSEARCH
# ------------------------------------------
up:
	@echo ">>> Starting OpenSearch..."
	docker compose up -d opensearch

	@echo ">>> Waiting until OpenSearch is ready..."
	@sleep 3
	@bash -c '\
	for i in {1..150}; do \
		if curl -s http://localhost:9200 >/dev/null; then \
			echo ">>> OpenSearch is ready!"; exit 0; \
		fi; \
		echo "Waiting for OpenSearch... ($$i/150)"; \
		sleep 2; \
	done; \
	echo ">>> ERROR: OpenSearch did not start!"; exit 1; \
	'

# ------------------------------------------
# FRONTEND (BACKGROUND + PID SAVE)
# ------------------------------------------
frontend:
	@echo ">>> Launching Frontend React App in background..."
	@bash -c '\
		cd ../frontend && \
		npm install && \
		nohup npm start > $(CUR_PATH)/frontend.log 2>&1 & \
		echo $$! > $(CUR_PATH)/frontend.pid \
	'
	@sleep 3
	@echo ">>> Frontend started ✓"

# ------------------------------------------
# BACKEND (BACKGROUND + PID SAVE)
# ------------------------------------------
api:
	@echo ">>> Starting Backend API in background..."
	@bash -c '\
		source activate $(ENV_NAME) && \
		nohup python -m app.main > $(CUR_PATH)/backend.log 2>&1 & \
		echo $$! > $(CUR_PATH)/backend.pid \
	'
	@sleep 2
	@echo ">>> Backend started ✓"

# ------------------------------------------
# LOG STREAM
# ------------------------------------------
logs:
	@echo ">>> Streaming backend logs..."
	@tail -f $(CUR_PATH)/backend.log

# ------------------------------------------
# STOP EVERYTHING (e.g. docker)
# ------------------------------------------
stop:
	@echo ">>> Stopping docker services…"
	docker compose down
	@echo ">>> Run 'make all' again to restart everything."

# ------------------------------------------
# FULL RESET (clean state)
# ------------------------------------------
reset:
	@echo ">>> Full reset..."
	docker compose down -v
	rm -f $(CUR_PATH)/frontend.pid $(CUR_PATH)/backend.pid $(CUR_PATH)/frontend.log $(CUR_PATH)/backend.log
	@echo ">>> Everything wiped. Use 'make all'."
