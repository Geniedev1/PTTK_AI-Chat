.PHONY: help build up down logs restart clean test

help:
	@echo "Available commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-staff     - View logs from staff-service"
	@echo "  make logs-customer  - View logs from customer-service"
	@echo "  make logs-cart      - View logs from cart-service"
	@echo "  make logs-product   - View logs from product-service"
	@echo "  make logs-gateway   - View logs from api-gateway"
	@echo "  make clean          - Stop services and clean volumes"
	@echo "  make test           - Run curl test examples"
	@echo "  make ps             - Show running containers"
	@echo "  make shell-staff    - Open shell in staff-service"
	@echo "  make shell-cart     - Open shell in cart-service"

build:
	docker-compose build

build-nocache:
	docker-compose build --no-cache

up:
	docker-compose up -d

down:
	docker-compose down

restart: down up

logs:
	docker-compose logs -f

logs-staff:
	docker-compose logs -f staff-service

logs-customer:
	docker-compose logs -f customer-service

logs-cart:
	docker-compose logs -f cart-service

logs-product:
	docker-compose logs -f product-service

logs-gateway:
	docker-compose logs -f api-gateway

clean:
	docker-compose down -v

ps:
	docker-compose ps

shell-staff:
	docker-compose exec staff-service bash

shell-customer:
	docker-compose exec customer-service bash

shell-cart:
	docker-compose exec cart-service bash

shell-product:
	docker-compose exec product-service bash

test:
	@bash curl-examples.sh

migrate-staff:
	docker-compose exec staff-service python manage.py migrate

migrate-customer:
	docker-compose exec customer-service python manage.py migrate

migrate-cart:
	docker-compose exec cart-service python manage.py migrate

migrate-product:
	docker-compose exec product-service python manage.py migrate

createsuperuser-staff:
	docker-compose exec staff-service python manage.py createsuperuser

createsuperuser-customer:
	docker-compose exec customer-service python manage.py createsuperuser

createsuperuser-cart:
	docker-compose exec cart-service python manage.py createsuperuser

createsuperuser-product:
	docker-compose exec product-service python manage.py createsuperuser
