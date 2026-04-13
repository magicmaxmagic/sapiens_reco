.PHONY: help build up down logs test clean db-reset

help:
	@echo "Sapiens Reco - Commandes Docker"
	@echo ""
	@echo "  make build    - Construire les images Docker"
	@echo "  make up       - Démarrer tous les services"
	@echo "  make down     - Arrêter tous les services"
	@echo "  make logs     - Voir les logs"
	@echo "  make test     - Lancer les tests backend"
	@echo "  make clean    - Nettoyer les conteneurs et volumes"
	@echo "  make db-reset - Réinitialiser la base de données"
	@echo ""

build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "✅ Services démarrés:"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	cd backend && python -m pytest tests/ -v

clean:
	docker-compose down -v
	docker system prune -f

db-reset:
	docker-compose down -v
	docker-compose up -d db
	@sleep 5
	docker-compose up -d backend

# Développement local sans Docker
.PHONY: dev-backend dev-frontend

dev-backend:
	cd backend && \
	python -m venv .venv && \
	. .venv/bin/activate && \
	pip install -r requirements.txt && \
	uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && \
	npm install && \
	npm run dev