#!/bin/sh

# экспорт переменных окружения для pipenv
env > .env

screen -dmS "chromium"
screen -S "chromium" -X stuff "nohup /usr/bin/chromium-browser --no-sandbox --disable-background-networking --disable-gpu --disable-default-apps --disable-extensions --disable-sync --disable-translate --disable-software-rasterizer --disable-dev-shm-usage --headless --hide-scrollbars --metrics-recording-only --mute-audio --no-first-run --safebrowsing-disable-auto-update --ignore-certificate-errors --ignore-ssl-errors --ignore-certificate-errors-spki-list --user-data-dir=/tmp --remote-debugging-port=$CHROME_WS_PORT --remote-debugging-address=$CHROME_WS_HOST\n"

pipenv run start
