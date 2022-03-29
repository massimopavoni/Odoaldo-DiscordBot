FROM python:3.10-slim-buster

WORKDIR Odoaldo-DiscordBot

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY bot/ bot/

ARG TOKEN
ENV DISCORD_BOT_TOKEN=$TOKEN

CMD [ "python", "bot/main.py" ] 
