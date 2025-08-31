.PHONY: run dev docker-up docker-down

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --reload

docker-up:
	docker compose --env-file .env.prod.example up --build -d

docker-down:
	docker compose down -v
