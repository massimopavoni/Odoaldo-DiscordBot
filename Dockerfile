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
