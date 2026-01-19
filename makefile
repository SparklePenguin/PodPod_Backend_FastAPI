-include .env

export SSH_USER
export SSH_KEY_PATH
export SERVER_IP

export BASE_YAML=./deploy/config/config.local.yaml

infra.connect: DB_PORT := $(shell yq '.database.port' ${BASE_YAML})
infra.connect: REDIS_PORT :=$(shell yq '.redis.port' ${BASE_YAML})
infra.connect:
	@echo "Kill ports if occupied..."
	@lsof -ti tcp:$(DB_PORT) | xargs -r kill -9 || true
	@lsof -ti tcp:$(REDIS_PORT) | xargs -r kill -9 || true

	@echo "Open SSH Tunnels..."
	ssh  -i ${SSH_KEY_PATH} -fN -L $(DB_PORT):127.0.0.1:$(DB_PORT) ${SSH_USER}@${SERVER_IP};
	ssh  -i ${SSH_KEY_PATH} -fN -L $(REDIS_PORT):127.0.0.1:$(REDIS_PORT) ${SSH_USER}@${SERVER_IP};

deploy.local:
	infisical run --env=dev --path=/backend -- docker-compose -f ./deploy/docker-compose.local.yml up --build

deploy.dev:
	infisical run --env=dev --path=/backend -- docker-compose -f ./deploy/docker-compose.dev.yml up --build -d

deploy.stg:
	infisical run --env=staging --path=/backend -- docker-compose -f ./deploy/docker-compose.stg.yml up --build -d

deploy.prd:
	infisical run --env=prod --path=/backend -- docker-compose -f ./deploy/docker-compose.prod.yml up --build -d