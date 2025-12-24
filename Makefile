PROJECT := rahusearch
COMPOSE := docker-compose.yml
PINGGY_PORT := 3000
API_HEALTH_URL := http://localhost:8000/health

.PHONY: up all stop restart predeploy predeploy-build


# -------------------------
# SAFE DEMO FLOW
# stop -> up -> wait api -> pinggy
# -------------------------
all:
	@echo "🧹 Stopping existing containers..."
	docker compose -p $(PROJECT) -f $(COMPOSE) down

	@echo "🚀 Starting runtime services..."
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d --build opensearch api frontend

	@echo "⏳ Waiting for OpenSearch..."
	@bash -c '\
	for i in {1..120}; do \
		if curl -s http://localhost:9200 >/dev/null; then \
			echo "✅ OpenSearch ready"; exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "❌ OpenSearch timeout"; exit 1;'

	@echo "⏳ Waiting for API..."
	@bash -c '\
	for i in {1..120}; do \
		if curl -s -o /dev/null -w "%{http_code}" $(API_HEALTH_URL) | grep -q 200; then \
			echo "✅ API ready"; exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "❌ API timeout"; exit 1;'

	@echo "🌍 Opening Pinggy tunnel..."
	ssh -p 443 -R 80:localhost:$(PINGGY_PORT) a.pinggy.io


# -------------------------
# FAST DEV FLOW (no down)
# -------------------------
up:
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d --build

predeploy-build:
	@echo "🛠️ Building predeploy image..."
	docker build -t rahusearch-predeploy -f pre_deploy/Dockerfile .

predeploy: predeploy-build
	@echo "📦 Running predeploy (index + embeddings, one-shot)..."
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d opensearch
	docker compose -p $(PROJECT) -f $(COMPOSE) run --rm predeploy
	docker compose -p $(PROJECT) -f $(COMPOSE) down

stop:
	docker compose -p $(PROJECT) -f $(COMPOSE) down

restart: stop up
