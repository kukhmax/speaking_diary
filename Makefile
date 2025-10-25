# Makefile для упрощения работы с Docker

.PHONY: help build up down restart logs clean backup restore test

# Цвета для вывода
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m

help: ## Показать эту справку
	@echo "$(GREEN)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

build: ## Собрать все контейнеры
	@echo "$(GREEN)Сборка контейнеров...$(NC)"
	docker-compose build

up: ## Запустить все сервисы
	@echo "$(GREEN)Запуск сервисов...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Сервисы запущены$(NC)"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:5000"
	@echo "pgAdmin:  http://localhost:5050"

down: ## Остановить все сервисы
	@echo "$(YELLOW)Остановка сервисов...$(NC)"
	docker-compose down

restart: ## Перезапустить все сервисы
	@echo "$(YELLOW)Перезапуск...$(NC)"
	docker-compose restart

logs: ## Показать логи всех сервисов
	docker-compose logs -f

logs-backend: ## Показать логи backend
	docker-compose logs -f backend

logs-frontend: ## Показать логи frontend
	docker-compose logs -f frontend

logs-db: ## Показать логи базы данных
	docker-compose logs -f db

ps: ## Показать статус контейнеров
	docker-compose ps

rebuild: ## Пересобрать и перезапустить
	@echo "$(GREEN)Пересборка...$(NC)"
	docker-compose up -d --build

clean: ## Остановить и удалить контейнеры
	@echo "$(YELLOW)Очистка контейнеров...$(NC)"
	docker-compose down
	docker system prune -f

clean-all: ## Удалить ВСЁ (включая volumes)
	@echo "$(YELLOW)ВНИМАНИЕ: Будут удалены все данные!$(NC)"
	@read -p "Продолжить? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker system prune -a -f; \
		echo "$(GREEN)✓ Очистка завершена$(NC)"; \
	fi

backup: ## Создать backup базы данных
	@echo "$(GREEN)Создание backup...$(NC)"
	@mkdir -p backups
	docker-compose exec -T db pg_dump -U diary_user diary_db > backups/diary_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Backup создан в директории backups/$(NC)"

restore: ## Восстановить базу данных из backup
	@echo "$(YELLOW)Доступные backups:$(NC)"
	@ls -1 backups/*.sql 2>/dev/null || echo "Нет доступных backups"
	@read -p "Введите имя файла backup: " backup_file; \
	if [ -f "backups/$$backup_file" ]; then \
		docker-compose exec -T db psql -U diary_user diary_db < backups/$$backup_file; \
		echo "$(GREEN)✓ Восстановление завершено$(NC)"; \
	else \
		echo "$(YELLOW)Файл не найден!$(NC)"; \
	fi

shell-backend: ## Войти в контейнер backend
	docker-compose exec backend bash

shell-db: ## Подключиться к PostgreSQL
	docker-compose exec db psql -U diary_user -d diary_db

test-api: ## Протестировать API
	@echo "$(GREEN)Тестирование API...$(NC)"
	@curl -s http://localhost:5000/api/health | python -m json.tool || echo "$(YELLOW)Backend не запущен$(NC)"

pgadmin-up: ## Запустить с pgAdmin
	docker-compose --profile tools up -d

stats: ## Показать статистику контейнеров
	docker stats --no-stream

check: ## Проверить что всё работает
	@echo "$(GREEN)Проверка сервисов...$(NC)"
	@echo -n "Backend:  "
	@curl -s http://localhost:5000/api/health > /dev/null && echo "$(GREEN)✓ OK$(NC)" || echo "$(YELLOW)✗ НЕ РАБОТАЕТ$(NC)"
	@echo -n "Frontend: "
	@curl -s http://localhost:3000 > /dev/null && echo "$(GREEN)✓ OK$(NC)" || echo "$(YELLOW)✗ НЕ РАБОТАЕТ$(NC)"
	@echo -n "Database: "
	@docker-compose exec -T db pg_isready -U diary_user > /dev/null && echo "$(GREEN)✓ OK$(NC)" || echo "$(YELLOW)✗ НЕ РАБОТАЕТ$(NC)"

dev: ## Запустить в режиме разработки
	docker-compose -f docker-compose.yml up

prod: ## Запустить в режиме продакшена
	docker-compose -f docker-compose.prod.yml up -d

install: ## Первоначальная установка
	@echo "$(GREEN)Установка Дневника...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Создание .env файла...$(NC)"; \
		cp .env.example .env; \
		echo "$(YELLOW)⚠ Отредактируйте .env файл перед запуском!$(NC)"; \
	fi
	@echo "$(GREEN)Сборка контейнеров...$(NC)"
	docker-compose build
	@echo "$(GREEN)Запуск сервисов...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Установка завершена!$(NC)"
	@echo ""
	@echo "Откройте: http://localhost:3000"

update: ## Обновить приложение
	@echo "$(GREEN)Обновление...$(NC)"
	git pull
	docker-compose up -d --build
	@echo "$(GREEN)✓ Обновление завершено$(NC)"