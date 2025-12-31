# =========================================
# FORCE BASH (REQUIRED FOR CONDA)
# =========================================
SHELL := /bin/bash

# =========================================
# GLOBAL CONFIG (ROOT LEVEL)
# =========================================

ENV_FILE := environment.yml
ENV_NAME := $(shell grep '^name:' $(ENV_FILE) | awk '{print $$2}')

CONDA_BASE := $(shell conda info --base)
CONDA_ACTIVATE := source $(CONDA_BASE)/etc/profile.d/conda.sh

PY := python

# SITES (noon excluded)
SITES := almanea extra jarir nahdi aldawaa

.DEFAULT_GOAL := help

# =========================================
# HELP
# =========================================
help:
	@echo ""
	@echo "Available targets:"
	@echo "  make env        -> create conda env if needed"
	@echo "  make all        -> run all scrapers (except noon)"
	@echo "  make almanea"
	@echo "  make extra"
	@echo "  make jarir"
	@echo "  make nahdi"
	@echo "  make aldawaa"
	@echo ""

# =========================================
# ENV SETUP
# =========================================
env:
	@echo ">>> Checking conda env: $(ENV_NAME)"
	@$(CONDA_ACTIVATE) && \
	if conda env list | awk '{print $$1}' | grep -qx "$(ENV_NAME)"; then \
		echo "✔ Conda env exists"; \
	else \
		echo "✚ Creating conda env $(ENV_NAME)"; \
		conda env create -f $(ENV_FILE); \
	fi

# =========================================
# GENERIC SCRAPER RUNNER
# =========================================
define RUN_SCRAPER
	@echo ""
	@echo "========================================="
	@echo "▶ Running $(1) scraper"
	@echo "========================================="
	@cd codes/$(1) && \
	$(CONDA_ACTIVATE) && \
	conda activate $(ENV_NAME) && \
	PYTHONPATH=$(PWD)/codes $(PY) scraper.py
endef

# =========================================
# SITE TARGETS
# =========================================
$(SITES): env
	$(call RUN_SCRAPER,$@)

# =========================================
# RUN ALL (except noon)
# =========================================
all: env
	@for site in $(SITES); do \
		$(MAKE) $$site; \
	done
