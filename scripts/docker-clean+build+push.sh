#!/bin/bash

. scripts/docker-env.sh
docker stop odoaldo odoaldo-mongo
docker rm odoaldo odoaldo-mongo
docker volume rm odoaldo_mongodata
docker network rm odoaldo_database
docker rmi $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot

docker build . -t $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot \
--build-arg DISCORD_TOKEN=$DISCORD_TOKEN \
--build-arg MONGO_USER=$MONGO_USER \
--build-arg MONGO_PASSWORD=$MONGO_PASSWORD \
--build-arg MONGO_HOST=$MONGO_HOST \
--build-arg MONGO_PORT=$MONGO_PORT

docker push $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot