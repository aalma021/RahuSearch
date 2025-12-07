# ------------------------------------------
# PREDEPLOY MAKEFILE (using shared OpenSearch)
# ------------------------------------------

ENV_NAME := $(shell grep "^name:" environment.yml | sed 's/name: //')
COMPOSE_FILE := ../backend/docker-compose.yml

.PHONY: all env up seed reset logs stop

# -------------------- MAIN TARGET --------------------
# make all => env + up + seed + stop
all: env up seed stop

# -------------------- Conda --------------------
env:
	@echo ">>> Checking Conda environment: $(ENV_NAME)"
	@if conda env list | grep -q "^$(ENV_NAME) "; then \
		echo ">>> Environment exists."; \
	else \
		echo ">>> Environment does not exist. Creating..."; \
		conda env create -f environment.yml; \
	fi

# -------------------- OpenSearch Up --------------------
up:
	@echo ">>> Starting global OpenSearch..."
	docker compose -f $(COMPOSE_FILE) up -d opensearch
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


# -------------------- Run Predeploy Loader --------------------
# -------------------- Run Predeploy Loader --------------------
seed:
	@echo ">>> Activating Conda environment: $(ENV_NAME)"
	@bash -c "source $$(conda info --base)/etc/profile.d/conda.sh && \
		conda activate $(ENV_NAME) && \
		echo '>>> Running Predeploy Loader (embedding + bulk upload)' && \
		python -m opensearch_client && \
		echo '>>> Seed completed.' && \
		conda deactivate"

# -------------------- Logs --------------------
logs:
	docker compose -f $(COMPOSE_FILE) logs -f opensearch

# -------------------- Stop --------------------
stop:
	@echo ">>> Stopping OpenSearch (data preserved)..."
	docker compose -f $(COMPOSE_FILE) down

# -------------------- Reset --------------------
reset:
	@echo ">>> Full Reset: Containers + Volume deleted!"
	docker compose -f $(COMPOSE_FILE) down -v
