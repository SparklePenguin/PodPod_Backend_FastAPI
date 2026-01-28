-include .env

export SSH_USER
export SSH_KEY_PATH
export SERVER_IP

export INFISICAL_TOKEN
export INFISICAL_PROJECT_ID

export BASE_YAML=./deploy/config/config.local.yaml

infra.connect: DB_PORT := $(shell yq '.database.port' ${BASE_YAML})
infra.connect: REDIS_PORT :=$(shell yq '.redis.port' ${BASE_YAML})
infra.connect:
	@echo "Kill ports if occupied..."
	@lsof -ti tcp:$(DB_PORT) | xargs -r kill -9 || true
	@lsof -ti tcp:$(REDIS_PORT) | xargs -r kill -9 || true

	@echo "Open SSH Tunnels..."
	ssh  -p ${SSH_PORT} -i ${SSH_KEY_PATH} -fN -L $(DB_PORT):127.0.0.1:$(DB_PORT) ${SSH_USER}@${SERVER_IP};
	ssh  -p ${SSH_PORT} -i ${SSH_KEY_PATH} -fN -L $(REDIS_PORT):127.0.0.1:$(REDIS_PORT) ${SSH_USER}@${SERVER_IP};

define deploy_with_infisical
	docker-compose -f $(1) down;
	infisical run \
		--projectId=$(INFISICAL_PROJECT_ID) \
		--env=$(2) \
		--path=/backend \
		-- \
		env DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 \
		docker-compose -f $(1) up --build -d
endef

deploy.local:
	docker-compose -f ./deploy/docker-compose.local.yml down;
	infisical run --env=dev --path=/backend -- docker-compose -f ./deploy/docker-compose.local.yml up --build

deploy.dev:
	$(call deploy_with_infisical,./deploy/docker-compose.dev.yml,dev)

deploy.stg:
	$(call deploy_with_infisical,./deploy/docker-compose.stg.yml,staging)

deploy.prd:
	$(call deploy_with_infisical,./deploy/docker-compose.prod.yml,prod)