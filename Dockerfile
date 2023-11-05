FROM alpine

WORKDIR Odoaldo-DiscordBot

COPY bot/ bot/
COPY requirements.txt .

RUN apk add ffmpeg python3 py3-pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del py3-pip && \
    apk cache clean && \
    addgroup -S nonroot && \
    adduser -S odoaldo -G nonroot

USER odoaldo

CMD python bot/main.py
