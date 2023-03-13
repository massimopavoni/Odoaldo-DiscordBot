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

FROM python:3.10-slim-buster

WORKDIR Odoaldo-DiscordBot

RUN apt-get -y update
RUN apt-get install -y ffmpeg

RUN python -m venv venv

COPY requirements.txt requirements.txt
COPY bot/ bot/

RUN . venv/bin/activate && pip install -r requirements.txt

ARG BOT_CONFIG \
    DISCORD_TOKEN \
    MONGO_USER \
    MONGO_PASSWORD \
    MONGO_HOST \
    MONGO_PORT
ENV BOT_CONFIG=$BOT_CONFIG \
    DISCORD_TOKEN=$DISCORD_TOKEN \
    MONGO_USER=$MONGO_USER \
    MONGO_PASSWORD=$MONGO_PASSWORD \
    MONGO_HOST=$MONGO_HOST \
    MONGO_PORT=$MONGO_PORT

CMD . venv/bin/activate && exec python bot/main.py
