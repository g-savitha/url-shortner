dev:
	uv run fastapi dev app/main.py

db:
	docker compose up -d

psql:
	docker compose exec db psql -U app -d shortener

desc:
	docker compose exec db psql -U app -d shortener -c "\d $(t)"
