#!/bin/bash

# chromium-browser \
#     --noerrdialogs \
#     --disable-infobars \ 
#     --disable-translate \
#     --no-first-run \
#     --fast \
#     --fast-start \
#     --aggressive-cache-discard \
#     --kiosk \
#         $1 &
chromium-browser --kiosk $1 &