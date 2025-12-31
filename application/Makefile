PROJECT := rahusearch
COMPOSE := docker-compose.yml
PINGGY_PORT := 3000
API_HEALTH_URL := http://localhost:8000/health

.PHONY: up all stop restart predeploy predeploy-build vllm-up vllm-stop add_data


# -------------------------
# SAFE DEMO FLOW
# stop -> up -> wait api -> pinggy
# -------------------------
all:
	@echo "🧹 Stopping existing containers..."
	docker compose -p $(PROJECT) -f $(COMPOSE) down

	@echo "🛑 Stopping vLLM if running..."
	@docker stop rahusearch-vllm || true

	@echo "🚀 Starting runtime services..."
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d --build weaviate api frontend

	@if [ "$(EMBED_RUNTIME)" = "local" ]; then \
		echo "🟢 EMBEDDING MODE: LOCAL (vLLM will be started)"; \
		$(MAKE) vllm-up; \
	else \
		echo "🔵 EMBEDDING MODE: EXTERNAL (vLLM will NOT be started)"; \
	fi

	@echo "⏳ Waiting for Weaviate..."
	@bash -c '\
	for i in {1..120}; do \
		if curl -s http://localhost:8080/v1/meta >/dev/null; then \
			echo "✅ Weaviate ready"; exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "❌ Weaviate timeout"; exit 1;'

	@echo "⏳ Waiting for API..."
	@bash -c '\
	for i in {1..120}; do \
		if curl -s -o /dev/null -w "%{http_code}" $(API_HEALTH_URL) | grep -q 200; then \
			echo "✅ API ready"; exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "❌ API timeout"; exit 1;'

	@echo "🌍 Opening Pinggy tunnel..."
	ssh -p 443 -R 80:localhost:$(PINGGY_PORT) a.pinggy.io


# -------------------------
# vLLM EMBEDDING SERVER
# -------------------------
vllm-up:
	@echo "🚀 Starting vLLM embedding server (CPU)..."
	@docker run -d --rm \
		--name rahusearch-vllm \
		--env-file .env \
		-p $(EMBED_PORT):8000 \
		vllm/vllm-openai:cpu \
		serve $$VLLM_MODEL \
		--runner $$VLLM_RUNNER \
		--port 8000 \
		--max-model-len $$VLLM_MAX_MODEL_LEN


vllm-stop:
	@echo "🛑 Stopping vLLM embedding server..."
	@docker stop rahusearch-vllm || true


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
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d weaviate
	docker compose -p $(PROJECT) -f $(COMPOSE) run --rm predeploy
	docker compose -p $(PROJECT) -f $(COMPOSE) down

add_data:
	@echo "➕ Running update service (add / upsert data)..."
	docker compose -p $(PROJECT) -f $(COMPOSE) up -d weaviate
	docker compose -p $(PROJECT) -f $(COMPOSE) run --rm update


stop:
	@docker stop rahusearch-vllm || true
	docker compose -p $(PROJECT) -f $(COMPOSE) down


restart: stop up
