#!/bin/bash

# Odoaldo-DiscordBot
# Copyright (C) 2021  Massimo Pavoni
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

. scripts/docker-build-env.sh
docker stop odoaldo odoaldo-mongo
docker rm odoaldo odoaldo-mongo
docker volume rm odoaldo_mongodata
docker network rm odoaldo_database
docker rmi $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot
docker build . -t $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot
docker push $DOCKERHUB_USER/$DOCKERHUB_REPOSITORY:odoaldo-discordbot
