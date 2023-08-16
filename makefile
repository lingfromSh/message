debug:
	@docker exec -ti message /bin/bash

i:
	pip3 install poetry && poetry install

dev:
	@poetry run sanic server:app --host 0.0.0.0 --workers 4

planner:
	@sanic planner:app --host 0.0.0.0 --port 8081 --workers 4