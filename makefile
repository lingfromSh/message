debug:
	@docker exec -ti message-message-1 /bin/bash

i:
	pip3 install poetry && poetry install

server:
	@poetry run sanic server:app --host 0.0.0.0 --workers 4

plan:
	@poetry run sanic planner:app --host 0.0.0.0 --port 8001 --workers 8

executor:
	@poetry run sanic executor:app --host 0.0.0.0 --port 8002 --fast

mongodb:
	docker exec -ti mongodb-primary /bin/bash