PROJECT := rahusearch
COMPOSE := docker-compose.yml
PINGGY_PORT := 3000
API_HEALTH_URL := http://localhost:8000/health

.PHONY: up all stop restart predeploy


# -------------------------
# SAFE DEMO FLOW
# stop -> up -> wait api -> pinggy
# -------------------------
all:
	@echo "🧹 Stopping existing containers (safe reset)..."
	docker compose -p $(PROJECT) -f $(COMPOSE) down

	@echo "🚀 Starting Docker services..."
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d --build

	@echo "⏳ Waiting for API to be ready..."
	@bash -c '\
	for i in {1..120}; do \
		if curl -s -o /dev/null -w "%{http_code}" $(API_HEALTH_URL) | grep -q 200; then \
			echo "✅ API is ready (200 OK)"; exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "❌ API did not become ready in time"; exit 1;'

	@echo ""
	@echo "🌍 Opening Pinggy tunnel for FRONTEND..."
	@echo "👉 Share the HTTPS link below with the client"
	@echo "------------------------------------------------"
	ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=5 \
	    -p 443 -R 80:localhost:$(PINGGY_PORT) a.pinggy.io

# -------------------------
# FAST DEV FLOW (no down)
# -------------------------
up:
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d --build

predeploy:
	@echo "📦 Running predeploy (index + embeddings, one-shot)..."
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d opensearch
	docker compose -p $(PROJECT) -f $(COMPOSE) run --rm predeploy
	docker compose -p $(PROJECT) -f $(COMPOSE) down

stop:
	docker compose -p $(PROJECT) -f $(COMPOSE) down

restart: stop up
