#!/bin/bash

. scripts/docker-build-env.sh
docker stop odoaldo odoaldo-mongo
docker rm odoaldo odoaldo-mongo
docker volume rm odoaldo_mongodata
docker network rm odoaldo_database
docker rmi $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot
docker buildx create --name odoaldo_multiarch --use --bootstrap
docker buildx build --push --platform linux/amd64,linux/arm64 -t $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot .
docker stop buildx_buildkit_odoaldo_multiarch0
docker rm buildx_buildkit_odoaldo_multiarch0
docker buildx rm odoaldo_multiarch
