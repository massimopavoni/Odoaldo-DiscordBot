#!/bin/bash

. $HOME/.local/bin/.odoaldo/docker-deploy-env.sh
docker stop odoaldo odoaldo-mongo
docker rm odoaldo odoaldo-mongo
docker network rm odoaldo_database
docker rmi $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot

docker pull $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot