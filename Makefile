.PHONY: help install dev build up down migrate shell test clean deploy

# Detect docker compose command
COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; else echo docker compose; fi)

help:
	@echo "Available commands:"
	@echo "  make install     - Install backend and frontend dependencies"
	@echo "  make dev         - Run development server (backend + frontend)"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start Docker containers"
	@echo "  make down        - Stop Docker containers"
	@echo "  make migrate     - Run Django migrations inside container"
	@echo "  make shell       - Open Django shell inside container"
	@echo "  make test        - Run Django tests inside container"
	@echo "  make clean       - Clean up Docker volumes and images"
	@echo "  make deploy      - Deploy to production"
	@echo "  make backup      - Backup database and media files"

install:
	pip install -r requirements.txt
	cd frontend && npm install

dev:
	@echo "Starting development servers..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:5173"
	python manage.py runserver &
	cd frontend && npm run dev

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

migrate:
	$(COMPOSE) exec backend python manage.py migrate

shell:
	$(COMPOSE) exec backend python manage.py shell

test:
	$(COMPOSE) exec backend python manage.py test

clean:
	$(COMPOSE) down -v
	docker system prune -f

deploy:
	./deploy.sh

backup:
	./backup.sh
