Установка зависимостей

```
pip install --no-cache-dir -r requirements.txt
```

Установка браузера

```
sudo add-apt-repository ppa:xtradeb/apps -y
sudo apt update
sudo apt install chromium
```

Настройка сервиса sysyemd

```
sudo nano /lib/systemd/system/patrik.service
```

```
[Unit]
Description=Patrik Start Service
Wants=graphical.target
After=graphical.target

[Service]
Environment=DISPLAY=:0.0
Environment=XAUTHORITY=/home/orangepi/.Xauthority
Type=forking
ExecStart=/bin/bash /home/orangepi/wifi-web/start.sh # СМЕНИ ИМЯ ПОЛЬЗОВАТЕЛЯ!!!
Restart=on-abort
User=orangepi
Group=orangepi

[Install]
WantedBy=graphical.target
```

```
sudo systemctl enable patrik.service
sudo systemctl stop patrik.service
```

Журнал ошибок

```
journalctl -xeu patrik.service
```