.PHONY: help install dev backend frontend test clean db-init admin

# Variables
BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV := $(BACKEND_DIR)/.venv
PYTHON := python3
UVICORN := uvicorn

# Couleurs
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
NC := \033[0m

help:
	@echo "$(BLUE)Sapiens Reco - Commandes Makefile$(NC)"
	@echo ""
	@echo "$(GREEN)Installation:$(NC)"
	@echo "  make install      - Installer toutes les dépendances"
	@echo "  make install-backend - Installer dépendances backend uniquement"
	@echo "  make install-frontend - Installer dépendances frontend uniquement"
	@echo ""
	@echo "$(GREEN)Développement:$(NC)"
	@echo "  make dev          - Démarrer backend + frontend"
	@echo "  make backend      - Démarrer uniquement le backend"
	@echo "  make frontend     - Démarrer uniquement le frontend"
	@echo ""
	@echo "$(GREEN)Base de données:$(NC)"
	@echo "  make db-init      - Initialiser la base de données locale"
	@echo "  make db-reset     - Réinitialiser la base de données"
	@echo "  make admin        - Créer un admin par défaut"
	@echo ""
	@echo "$(GREEN)Tests:$(NC)"
	@echo "  make test         - Lancer tous les tests"
	@echo "  make test-backend - Lancer tests backend uniquement"
	@echo "  make lint         - Vérifier le code (ruff)"
	@echo ""
	@echo "$(GREEN)Nettoyage:$(NC)"
	@echo "  make clean        - Nettoyer les fichiers temporaires"
	@echo "  make clean-all    - Nettoyer tout (y compris venv/node_modules)"
	@echo ""

# Installation
install: install-backend install-frontend
	@echo "$(GREEN)✅ Installation terminée$(NC)"

install-backend:
	@echo "$(BLUE)📦 Installation backend...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m venv .venv
	. $(VENV)/bin/activate && pip install -r requirements.txt
	@echo "$(GREEN)✅ Backend installé$(NC)"

install-frontend:
	@echo "$(BLUE)📦 Installation frontend...$(NC)"
	cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✅ Frontend installé$(NC)"

# Développement
dev: backend frontend
	@echo "$(GREEN)✅ Services démarrés$(NC)"

backend:
	@echo "$(BLUE)🚀 Démarrage backend...$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(NC)"
	cd $(BACKEND_DIR) && \
	. $(VENV)/bin/activate && \
	export DATABASE_URL="sqlite:///./local.db" && \
	export AUTH_REQUIRED="true" && \
	export ADMIN_USERNAME="admin" && \
	export ADMIN_PASSWORD="AdminPass123" && \
	export JWT_SECRET_KEY="local-dev-secret-key-min-32-chars-long" && \
	export APP_ENV="development" && \
	export AUTO_CREATE_TABLES="true" && \
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	@echo "$(BLUE)🚀 Démarrage frontend...$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	cd $(FRONTEND_DIR) && npm run dev

# Base de données
db-init:
	@echo "$(BLUE)📊 Initialisation base de données...$(NC)"
	cd $(BACKEND_DIR) && \
	. $(VENV)/bin/activate && \
	export DATABASE_URL="sqlite:///./local.db" && \
	export AUTO_CREATE_TABLES="true" && \
	$(PYTHON) -c "from app.core.database import engine; from app.models import Base; Base.metadata.create_all(engine); print('✅ Tables créées')"
	@echo "$(GREEN)✅ Base de données initialisée$(NC)"

db-reset:
	@echo "$(YELLOW)🗑️  Suppression base de données...$(NC)"
	rm -f $(BACKEND_DIR)/local.db $(BACKEND_DIR)/test.db $(BACKEND_DIR)/test_audit.jsonl
	@$(MAKE) db-init

admin:
	@echo "$(BLUE)👤 Création admin...$(NC)"
	@echo "$(YELLOW)Username: admin$(NC)"
	@echo "$(YELLOW)Password: AdminPass123$(NC)"
	curl -s -X POST http://localhost:8000/api/auth/signup \
		-H "Content-Type: application/json" \
		-d '{"username":"admin","password":"AdminPass123","email":"admin@optimus.com","role":"admin"}'
	@echo ""
	@echo "$(GREEN)✅ Admin créé$(NC)"

# Tests
test: test-backend
	@echo "$(GREEN)✅ Tests terminés$(NC)"

test-backend:
	@echo "$(BLUE)🧪 Tests backend...$(NC)"
	cd $(BACKEND_DIR) && \
	. $(VENV)/bin/activate && \
	export DATABASE_URL="sqlite:///./test.db" && \
	export AUTH_REQUIRED="true" && \
	export ADMIN_USERNAME="admin" && \
	export ADMIN_PASSWORD="TestAdmin#2026Secure" && \
	export JWT_SECRET_KEY="test-secret-key" && \
	export AUTO_CREATE_TABLES="true" && \
	pytest tests/ -v --tb=short

lint:
	@echo "$(BLUE)🔍 Vérification code...$(NC)"
	cd $(BACKEND_DIR) && \
	. $(VENV)/bin/activate && \
	ruff check app/ tests/
	@echo "$(GREEN)✅ Code OK$(NC)"

# Nettoyage
clean:
	@echo "$(BLUE)🧹 Nettoyage...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -f $(BACKEND_DIR)/local.db $(BACKEND_DIR)/test.db $(BACKEND_DIR)/test_audit.jsonl 2>/dev/null || true
	@echo "$(GREEN)✅ Nettoyé$(NC)"

clean-all: clean
	@echo "$(YELLOW)🗑️  Suppression venv/node_modules...$(NC)"
	rm -rf $(BACKEND_DIR)/.venv
	rm -rf $(FRONTEND_DIR)/node_modules
	@echo "$(GREEN)✅ Tout nettoyé$(NC)"

# Raccourcis
run: dev
up: dev
start: dev