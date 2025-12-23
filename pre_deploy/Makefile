# ------------------------------------------
# PREDEPLOY MAKEFILE (DOCKER-BASED)
# ------------------------------------------

PROJECT := rahusearch
COMPOSE := ../docker-compose.yml
PREDEPLOY_IMAGE := rahusearch-predeploy

.PHONY: all up build seed stop reset logs

# Full flow
all: up build seed stop

# Start OpenSearch (shared)
up:
	@echo "🚀 Starting shared OpenSearch..."
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d opensearch
	@echo "⏳ Waiting for OpenSearch..."
	@bash -c '\
	for i in {1..300}; do \
		if curl -s http://localhost:9200 >/dev/null; then \
			echo "✅ OpenSearch ready"; exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "❌ OpenSearch not ready"; exit 1;'

# Build predeploy image
build:
	docker build -t $(PREDEPLOY_IMAGE) -f Dockerfile ..

# Run predeploy loader
seed:
	@echo "📦 Running predeploy (embedding + bulk upload)..."
	docker run --rm \
	  --network host \
	  --env-file ../.env \
	  $(PREDEPLOY_IMAGE)

# Logs (OpenSearch)
logs:
	docker compose -p $(PROJECT) -f $(COMPOSE) logs -f opensearch

# Stop services (data preserved)
stop:
	docker compose -p $(PROJECT) -f $(COMPOSE) down

# Full reset (DANGER)
reset:
	docker compose -p $(PROJECT) -f $(COMPOSE) down -v
