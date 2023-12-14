dev:
	@cd devops/docker-compose && docker compose --profile debug --profile standalone up

build:
	@cd devops/docker-compose && docker compose --profile debug --profile standalone build --build-arg VERSION=0.0.1

clean:
	@cd devops/docker-compose && docker compose --profile debug --profile standalone down
