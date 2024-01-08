#!/bin/bash

export DISPALY=:0
# chromium-browser --noerrdialogs --disable-infobars --disable-translate --no-first-run --fast --fast-start --aggressive-cache-discard --kiosk $1 &
if command -v chromium-browser > /dev/null; then
    chromium-browser --kiosk $1 &
else
    chromium --kiosk $1 &
fi