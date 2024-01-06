import os
import sys
import time
import asyncio
import logging
import requests
# import webbrowser

from uuid import UUID, uuid4
from random import randint
from logging.handlers import RotatingFileHandler
from subprocess import Popen, PIPE, TimeoutExpired

from hypercorn.asyncio import serve
from hypercorn.config import Config
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


SPEECH_SERVER_URL = "http://localhost:8006/say"
WIFI_ADAPTER_NAME = "wlp0s20f3"
AP_NAME = "patrik"
AP_SSID = f"{AP_NAME}-{randint(99, 999)}"
AP_PASSWORD = "12345678"
CONNECTION_TIMEOUT = 5
NMCLI_TIMEOUT = 0.1
WAIT_ADDRESS_TIMEOUT = 2

 
app = FastAPI()

config = Config()
config.bind = ["localhost:8888"]

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

if not os.path.exists("logs"):
    os.makedirs("logs")

log_file = RotatingFileHandler(
    'logs/connect_wifi.log',
    maxBytes=32768, 
    backupCount=16
)
log_console = logging.StreamHandler()

logging.basicConfig(
    handlers=(log_file, log_console), 
    format='[%(asctime)s | %(levelname)s]: %(message)s', 
    datefmt='%m.%d.%Y %H:%M:%S',
    level=logging.INFO
)


class SSID(BaseModel):
    text: str
    value: UUID = Field(default_factory=uuid4)


class Credintals(BaseModel):
    ssid: str
    password: str


def create_ap():
    cmds = [
        f"nmcli con delete {AP_NAME}",
        f"nmcli con add type wifi ifname {WIFI_ADAPTER_NAME} con-name {AP_NAME} autoconnect yes ssid {AP_SSID}",
        f"nmcli con mod {AP_NAME} 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared",
        f"nmcli con mod {AP_NAME} wifi-sec.key-mgmt wpa-psk",
        f"nmcli con mod {AP_NAME} wifi-sec.psk {AP_PASSWORD}"
    ]

    for cmd in cmds:
        Popen(cmd, shell=True)
        time.sleep(NMCLI_TIMEOUT)


def turn_on_ap():
    Popen(f"nmcli con up {AP_NAME}", shell=True)


def is_ap_exists():
    con_list_raw = Popen(
        ["nmcli -t -f NAME con"],
        shell=True,
        stdout=PIPE
    )
    con_list, err = con_list_raw.communicate()

    if err:
        logging.error(err)

    for con_name in con_list.decode("utf-8").rsplit("\n"):
        if con_name == AP_NAME:
            return True
    
    return False


def get_ip_address():
    connectio_info_raw = Popen(
        [f"nmcli -t con show {AP_NAME} | grep IP4.ADDRESS"],
        shell=True,
        stdout=PIPE
    )
    ip_addr_raw, err = connectio_info_raw.communicate()

    if err:
        logging.error(err)

    ip_addr = ip_addr_raw.decode("utf-8").split(":")[1].split("/")[0].split(".")
    return ". ". join(ip_addr)


def say_connect_params():
    time.sleep(WAIT_ADDRESS_TIMEOUT)

    phrase = (
        f"Имя моей Wi-Fi сети {AP_SSID}, пароль {'. '.join(AP_PASSWORD)}. "
        f"Мой статический IP адрес {get_ip_address()}"
    )
    try:
        r = requests.post(SPEECH_SERVER_URL, json={"phrase": phrase})
        print(r)
    except requests.exceptions.ConnectionError:
        logging.error(f"No connection to speech server {SPEECH_SERVER_URL}")


@app.post("/connect/")
async def connect(credintals: Credintals):
    nmcli = Popen([
            f"nmcli",
            f"dev",
            f"wifi",
            f"connect",
            f"{credintals.ssid}",
            f"password",
            f"{credintals.password}"
        ], 
        stderr=PIPE,
        stdout=PIPE
    )

    err_msg = f"Не удалось подключиться к сети {credintals.ssid}"
    
    try:
        answer, err = nmcli.communicate(timeout=CONNECTION_TIMEOUT)
    except TimeoutExpired:
        nmcli.kill()
        logging.error(err_msg)

        return {"message": err_msg}

    if err and err.split()[0] == b"Error:":
        if answer:
            logging.info(answer)
        logging.error(err_msg)
        logging.error(err)

        return {"message": err_msg}
    
    url = sys.argv[1]
    if url:
        logging.info(f"Openning url: {url}")
        # webbrowser.get(using='chromium-browser').open_new_tab(url)
        Popen(
            [f"sh ./start-browser.sh {url}"],
            shell=True,
            stdout=PIPE
        )
        exit(0)
    exit(0)


@app.get("/ssid/")
async def scan_ssid() -> list[SSID]:
    iwlist_raw = Popen(
        ["nmcli -t -f active,ssid dev wifi"],
        shell=True,
        stdout=PIPE
    )
    ap_list, err = iwlist_raw.communicate()
    ap_array = []

    if err:
        logging.error(err)

    for line in ap_list.decode("utf-8").rsplit("\n"):
        try:
            _, ap_ssid = line.split(":")
            if ap_ssid:
                ap_array.append(SSID(text=ap_ssid))
        except ValueError:
            continue
    
    return ap_array


if __name__ == "__main__":
    # if not is_ap_exists():
    create_ap()
    turn_on_ap()
    say_connect_params()
    
    # Serve static files
    app.mount("/", StaticFiles(directory="static/dist", html=True))
    # Run main application
    asyncio.run(serve(app, config))