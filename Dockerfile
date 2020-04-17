FROM python:3.7.4-alpine3.9

RUN mkdir /code
WORKDIR /code
COPY . /code

RUN mkdir /var/screenshots

ENV SCREENSHOT_PATH=/var/screenshots
ENV FILENAME_PREFIX=web2img

ENV WEB_SERVER_HOST="0.0.0.0"
ENV WEB_SERVER_PORT=8899

ENV CHROME_WS_HOST="0.0.0.0"
ENV CHROME_WS_PORT=18222
ENV CHROME_UA="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0"

ENV DOCUMENT_READY_TIMEOUT=30
ENV ANIMATION_READY_TIMEOUT=5
ENV READY_ELEMENT_ID="fuWaequee3GohquaiQu5"

RUN apk add screen

RUN echo @edge http://nl.alpinelinux.org/alpine/edge/community >> /etc/apk/repositories \
    && echo @edge http://nl.alpinelinux.org/alpine/edge/main >> /etc/apk/repositories \
    && apk add --no-cache \
        chromium@edge \
        harfbuzz@edge \
        nss@edge \
        freetype@edge \
        ttf-freefont@edge

RUN pip3 install pipenv
RUN pipenv install

# Чистим мусор после установки
RUN rm -rf /var/cache/*
RUN mkdir /var/cache/apk

ENTRYPOINT ./entrypoint.sh