# Makefile
.PHONY: build run stop logs clean

# Build the Docker image
build:
	docker compose build

# Run the container
run:
	docker compose up -d

# Stop the container
stop:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Clean up
clean:
	docker compose down -v
	docker image prune -f

# Run scraper immediately (for testing)
test-run:
	docker compose exec scraper python /app/run_scraper.py

# Access container bash
bash:
	docker compose exec scraper bash

# Check container health
health:
	curl http://localhost:8080/health