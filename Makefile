.PHONY: up down restart logs model frontend-install frontend-run clean help

help:
	@echo "Available commands:"
	@echo "  make up               - Start Backend, DB, and Ollama (Docker)"
	@echo "  make down             - Stop all containers"
	@echo "  make restart          - Restart containers"
	@echo "  make logs             - View Backend logs"
	@echo "  make model            - Pull Llama 3.2 model into Ollama container (Run once)"
	@echo "  make frontend-install - Install Frontend node modules"
	@echo "  make frontend-run     - Start Frontend Dev Server"
	@echo "  make clean            - Stop containers and remove volumes (Resets DB)"

up:
	docker-compose up --build -d
	@echo "Backend API running at http://localhost:8050"

down:
	docker-compose down

restart: down up

logs:
	docker-compose logs -f backend

model:
	@echo "Pulling Llama 3.2 model... (This may take a while)"
	docker exec -it stock_ollama ollama run llama3.2

frontend-install:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev

clean:
	docker-compose down -v
