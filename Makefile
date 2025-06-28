# Makefile для Гряг-бота
.PHONY: help install install-dev setup format lint test clean run docker-build docker-run

# Кольори для виводу
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показати це повідомлення допомоги
	@echo "$(GREEN)🤖 Гряг-бот - Makefile команди$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Встановити основні залежності
	@echo "$(GREEN)📦 Встановлення основних залежностей...$(NC)"
	pip install -r requirements.txt

install-dev: install ## Встановити залежності для розробки
	@echo "$(GREEN)🛠️  Встановлення dev залежностей...$(NC)"
	pip install -r requirements-dev.txt
	pre-commit install

setup: install-dev ## Повне налаштування середовища розробки
	@echo "$(GREEN)🚀 Налаштування середовища розробки...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)⚠️  Копіюю .env.example -> .env$(NC)"; \
		cp .env.example .env; \
		echo "$(RED)❗ Будь ласка, відредагуйте .env файл з вашими токенами$(NC)"; \
	fi
	mkdir -p data logs backups
	@echo "$(GREEN)✅ Середовище готове до роботи!$(NC)"

format: ## Форматування коду
	@echo "$(GREEN)🎨 Форматування коду...$(NC)"
	black bot/ tests/ *.py
	isort bot/ tests/ *.py

lint: ## Перевірка коду лінтерами
	@echo "$(GREEN)🔍 Перевірка коду...$(NC)"
	black --check bot/ tests/ *.py
	isort --check-only bot/ tests/ *.py
	flake8 bot/ tests/ *.py
	mypy bot/
	bandit -r bot/ -f json -o bandit-report.json || true
	safety check

test: ## Запуск тестів
	@echo "$(GREEN)🧪 Запуск тестів...$(NC)"
	pytest -v --cov=bot --cov-report=term-missing

test-quick: ## Швидкі тести (без coverage)
	@echo "$(GREEN)⚡ Швидкі тести...$(NC)"
	pytest -v -x

clean: ## Очистка тимчасових файлів
	@echo "$(GREEN)🧹 Очистка...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/ bandit-report.json
	rm -rf *.egg-info build/ dist/

run: ## Запуск бота
	@echo "$(GREEN)🤖 Запуск Гряг-бота...$(NC)"
	python -m bot.main

run-dev: ## Запуск бота в режимі розробки
	@echo "$(GREEN)🔧 Запуск в режимі розробки...$(NC)"
	python start.py

check-deps: ## Перевірка залежностей
	@echo "$(GREEN)📋 Перевірка залежностей...$(NC)"
	pip check
	safety check

docker-build: ## Збірка Docker образу
	@echo "$(GREEN)🐳 Збірка Docker образу...$(NC)"
	docker build -t gryag-bot .

docker-run: ## Запуск Docker контейнера
	@echo "$(GREEN)🐳 Запуск Docker контейнера...$(NC)"
	docker-compose up -d

docker-logs: ## Перегляд логів Docker
	@echo "$(GREEN)📋 Логи Docker контейнера...$(NC)"
	docker-compose logs -f

docker-stop: ## Зупинка Docker контейнера
	@echo "$(GREEN)🛑 Зупинка Docker контейнера...$(NC)"
	docker-compose down

pre-commit: format lint test ## Виконати всі перевірки перед коммітом
	@echo "$(GREEN)✅ Всі перевірки пройдені!$(NC)"

analyze: ## Аналіз коду та статистика
	@echo "$(GREEN)📊 Аналіз проекту...$(NC)"
	@echo "Рядків коду в bot/:"
	@find bot/ -name "*.py" -exec wc -l {} + | tail -1
	@echo "Кількість файлів:"
	@find bot/ -name "*.py" | wc -l
	@echo "TODOs та FIXMEs:"
	@grep -r "TODO\|FIXME" bot/ || echo "Не знайдено"

backup: ## Створити backup
	@echo "$(GREEN)💾 Створення backup...$(NC)"
	python -c "from bot.modules.backup_manager import BackupManager; BackupManager().create_backup()"

# Спеціальні цілі для локального аналізатора
install-local-deps: ## Встановити залежності локального аналізатора
	@echo "$(GREEN)🧠 Встановлення залежностей локального аналізатора...$(NC)"
	pip install sentence-transformers spacy
	python -m spacy download uk_core_news_sm || echo "Українська модель недоступна, використовується англійська"
	python -m spacy download en_core_web_sm

test-local-analyzer: ## Тест локального аналізатора
	@echo "$(GREEN)🧠 Тестування локального аналізатора...$(NC)"
	python -c "from bot.modules.local_analyzer import get_analyzer; print('✅ Локальний аналізатор працює')"

# Цілі для CI/CD
ci: lint test ## CI пайплайн
	@echo "$(GREEN)🔄 CI пайплайн завершено$(NC)"

build-release: clean test docker-build ## Повна збірка релізу
	@echo "$(GREEN)🎉 Реліз готовий!$(NC)"

# Нові команди для покращень Фази 1
monitor: ## Запуск веб-дашборду моніторингу
	@echo "$(GREEN)📊 Запуск веб-дашборду...$(NC)"
	python -c "from bot.modules.web_dashboard import start_dashboard; start_dashboard()"

validate-config: ## Валідація конфігурації
	@echo "$(GREEN)🔧 Валідація конфігурації...$(NC)"
	python -c "from bot.modules.config_validator import ConfigValidator; ConfigValidator().validate_all()"
