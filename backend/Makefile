# ------------------------------------------
# MAKEFILE (Production-Ready, Python Script)
# ------------------------------------------

# Extract environment name from environment.yml
ENV_NAME := $(shell grep "^name:" environment.yml | sed 's/name: //')
API_PATH := app/main.py

.PHONY: all env up api logs stop reset

# ------------------------------------------
# DEFAULT TARGET
# ------------------------------------------
all: env up api

# ------------------------------------------
# 1) Create Conda Environment (if missing)
# ------------------------------------------
env:
	@echo ">>> Checking Conda environment: $(ENV_NAME)"
	@if conda env list | grep -q "^$(ENV_NAME) "; then \
		echo ">>> Environment exists."; \
	else \
		echo ">>> Environment does not exist. Creating..."; \
		conda env create -f environment.yml; \
	fi

# ------------------------------------------
# 2) Start OpenSearch (Docker)
# ------------------------------------------
up:
	@echo ">>> Starting OpenSearch (shared volume from predeploy)..."
	docker compose up -d opensearch

	@echo ">>> Waiting for OpenSearch to be ready..."

	@bash -c '\
	for i in {1..300}; do \
		if curl -s http://localhost:9200 >/dev/null; then \
			echo ">>> OpenSearch is ready!"; \
			exit 0; \
		fi; \
		echo ">>> Waiting for OpenSearch... ($$i/300)"; \
		sleep 2; \
	done; \
	echo ">>> ERROR: OpenSearch did not become ready in time"; \
	exit 1;'

# ------------------------------------------
# 3) Start API Locally (Foreground Logs)
# ------------------------------------------
api:
	@echo ">>> Activating conda env and starting API..."
	@bash -c "source activate $(ENV_NAME) && python -m app.main"

# -------------------- FRONTEND --------------------
frontend:
	@echo ">>> Starting Frontend React App..."
	@bash -c '\
		cd ../frontend && \
		echo ">>> Installing dependencies if needed..." && \
		npm install && \
		echo ">>> Starting frontend with npm start..." && \
		npm start \
	'

# ------------------------------------------
# 4) OpenSearch Live Logs
# ------------------------------------------
logs:
	docker compose logs -f opensearch

# ------------------------------------------
# 5) Stop All Services (Keep Data)
# ------------------------------------------
stop:
	@echo ">>> Stopping containers (data preserved)..."
	docker compose down

# ------------------------------------------
# 6) FULL RESET (Delete Containers + Volume)
# ------------------------------------------
reset:
	@echo ">>> WARNING: Removing OpenSearch containers + shared data volume!"
	docker compose down -v
