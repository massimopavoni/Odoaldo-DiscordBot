#!/bin/bash

. scripts/docker-build-env.sh
docker stop odoaldo odoaldo-mongo
docker rm odoaldo odoaldo-mongo
docker volume rm odoaldo_mongodata
docker network rm odoaldo_database
docker rmi $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot
docker build . -t $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot
docker push $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot
