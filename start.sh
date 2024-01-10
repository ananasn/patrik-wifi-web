#!/bin/bash
# sleep 30
# sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' /home/pi/.config/chromium/Default/Preferences
# sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' /home/pi/.config/chromium/Default/Preferences
# xset -dpms       # Turn off dpms blanking until next boot
# xset s activate  # Force screen blank
# xset s 1         # Blank screen again if key or mouse is moved.

# sleep 30         # Allow time for booting and starting browser. Adjust as necessary
# xset s reset     # Force screen on
# xset s 0         # Disable blanking until next boot

MAIN_URL="http://ya.ru"  # CHANGE ME PLEASE!!!
WIFI_URL="http://localhost:8888"
LOADER_URL="loader.html"

sh ./start-browser.sh $LOADER_URL &

# Stop all hotspot
# nmcli con delete patrik

# Forget all wi-fi networks
# nmcli --terse connection show | cut -d : -f 1 | \
#   while read name; do echo nmcli connection delete "$name"; done

# Check if wifi connection is established
WIFI_CONNECTED=`nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d\' -f2`

cd /home/$USER/wifi-web

if test -z "$WIFI_CONNECTED"; then
    python3 ./connect_wifi.py $MAIN_URL &
    sleep 25
    sh ./start-browser.sh $WIFI_URL &
else
    echo Opening main interface
    sh ./start-browser.sh $MAIN_URL &

    # sleep 30         # Allow time for booting and starting browser. Adjust as necessary
    # xset s reset     # Force screen on
    # xset s 0         # Disable blanking until next boot
fi



