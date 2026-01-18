

run.dev:
	sudo infisical run --env=dev --path=/backend -- docker-compose -f ./deploy/docker-compose.dev.yml up --build

run.stg:
	sudo infisical run --env=staging --path=/backend -- docker-compose -f ./deploy/docker-compose.stg.yml up --build