

deploy.dev:
	infisical run --env=dev --path=/backend -- docker-compose -f ./deploy/docker-compose.dev.yml up --build -d

deploy.stg:
	infisical run --env=staging --path=/backend -- docker-compose -f ./deploy/docker-compose.stg.yml up --build -d

deploy.prd:
	infisical run --env=prod --path=/backend -- docker-compose -f ./deploy/docker-compose.prod.yml up --build -d