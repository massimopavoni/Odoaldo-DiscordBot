FROM alpine

WORKDIR Odoaldo-DiscordBot

COPY bot/ bot/
COPY requirements.txt .

RUN apk add --no-cache --virtual .tmp-build-deps \
    gcc libc-dev libffi-dev python3-dev py3-pip && \
    apk add ffmpeg python3 && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .tmp-build-deps && \
    addgroup -S nonroot && \
    adduser -S odoaldo -G nonroot

USER odoaldo

CMD python bot/main.py
