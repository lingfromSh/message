debug:
	@docker exec -ti message /bin/bash

i:
	pip3 install poetry && poetry install

dev:
	@sanic server:app --host 0.0.0.0 --dev