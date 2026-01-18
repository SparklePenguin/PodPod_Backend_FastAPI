

run.dev:
	infisical run --env=dev --path=/backend -- docker-compose -f ./deploy/docker-compose.dev.yml up --build -ㅇ

run.stg:
	infisical run --env=staging --path=/backend -- docker-compose -f ./deploy/docker-compose.stg.yml up --build -d