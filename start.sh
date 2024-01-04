#!/bin/bash
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

# Check if wifi connection is established
WIFI_CONNECTED=`nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d\' -f2`

cd /home/$USER/wifi-web

if test -z "$WIFI_CONNECTED"; then
    python3 ./connect_wifi.py $MAIN_URL &
    sleep 2
    sh ./start-browser.sh $WIFI_URL
else
    echo Opening main interface
    sh ./start-browser.sh $MAIN_URL

    # sleep 30         # Allow time for booting and starting browser. Adjust as necessary
    # xset s reset     # Force screen on
    # xset s 0         # Disable blanking until next boot
fi



