import os
import sys
import time
import yaml
import pickle
import asyncio
import logging
import tempfile 
import requests

from pathlib import Path
from uuid import UUID, uuid4
from random import randint
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from subprocess import Popen, PIPE, TimeoutExpired

from hypercorn.asyncio import serve
from hypercorn.config import Config
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# Set path for script.
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Create a temporary file for SSIDs list.
tmp_file = tempfile.NamedTemporaryFile()

# Load config file.
with open("config.yaml") as cfg_file:
    cfg = yaml.load(cfg_file, Loader=yaml.SafeLoader)


# Configure global constants.
SPEECH_SERVER_URL = cfg["speech_server"]["url"]
WAIT_ADDRESS_TIMEOUT = cfg["speech_server"]["wait_address_timeout"]

AP_ADAPTER_NAME = cfg["hotspot"]["adapter_name"]
AP_NAME = cfg["hotspot"]["connection_name"]
AP_SSID = f"{AP_NAME}-{randint(99, 999)}"
AP_PASSWORD = cfg["hotspot"]["password"]

NMCLI_CONNECTION_TIMEOUT = cfg["nmcli"]["connection_timeout"]
NMCLI_EXEC_TIMEOUT = cfg["nmcli"]["exec_timeout"]

# Configure logging.
log_dir = Path(cfg["logging"]["log_dir"])
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = RotatingFileHandler(
    log_dir / cfg["logging"]["log_file"],
    maxBytes=cfg["logging"]["max_bytes"], 
    backupCount=cfg["logging"]["backup_count"]
)
log_console = logging.StreamHandler()

logging.basicConfig(
    handlers=(log_file, log_console), 
    format=cfg["logging"]["log_format"], 
    datefmt=cfg["logging"]["date_format"],
    level=logging.getLevelName(cfg["logging"]["log_level"])
)

sys.tracebacklimit = 0


class SSID(BaseModel):
    text: str
    value: UUID = Field(default_factory=uuid4)


class Credintals(BaseModel):
    ssid: str
    password: str


def scan_ssid():
    Popen([f"nmcli con delete {AP_NAME}"], shell=True)
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
            if ap_ssid and not ap_ssid.startswith(AP_NAME):
                ap_array.append(SSID(text=ap_ssid))
        except ValueError:
            continue

    if len(ap_array) > 1:
        with open(tmp_file.name, "wb") as tf:
            pickle.dump(ap_array, tf)

    if len(ap_array) == 1:
        with open(tmp_file.name, "rb") as tf:
            ap_array = pickle.load(tf)

    return ap_array


def create_ap():
    cmds = [
        f"nmcli con down {AP_NAME}",
        f"nmcli con add type wifi ifname {AP_ADAPTER_NAME} con-name {AP_NAME} autoconnect yes ssid {AP_SSID}",
        f"nmcli con mod {AP_NAME} 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared",
        f"nmcli con mod {AP_NAME} wifi-sec.key-mgmt wpa-psk",
        f"nmcli con mod {AP_NAME} wifi-sec.psk {AP_PASSWORD}"
    ]

    for cmd in cmds:
        Popen(cmd, shell=True)
        time.sleep(NMCLI_EXEC_TIMEOUT)


def turn_on_ap():
    Popen(f"nmcli con up {AP_NAME}", shell=True)


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
        f"Привет, меня зовут Патрик."
        f"Имя моей Wi-Fi сети {AP_SSID}, пароль {'. '.join(AP_PASSWORD)}. "
        f"Мой статический IP адрес {get_ip_address()}"
    )
    try:
        r = requests.post(SPEECH_SERVER_URL, json={"phrase": phrase})
        if r.status_code != 200:
            logging.error("Speech server returns non OK answer")
    except requests.exceptions.ConnectionError:
        logging.error(f"No connection to speech server {SPEECH_SERVER_URL}")


# Configure FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    scan_ssid()
    create_ap()
    turn_on_ap()
    say_connect_params()

    yield


app = FastAPI(lifespan=lifespan)

app_config = Config()
app_config.bind = [cfg["fastapi_server"]["url"]]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg["fastapi_server"]["origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/connect/")
async def connect(credintals: Credintals):
    Popen([f"nmcli con delete {AP_NAME}"], shell=True)
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
        answer, err = nmcli.communicate(timeout=NMCLI_CONNECTION_TIMEOUT)
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
    
    try:
        url = sys.argv[1]
        logging.info(f"Openning url: {url}")
        Popen([f"sh ./start-browser.sh {url}"], shell=True)
    except:
        logging.error("URL is not correct or not provided")
    finally:
        os.kill(os.getpid(), 9)


@app.get("/ssid/")
async def ssid() -> list[SSID]:
    return scan_ssid()
    

if __name__ == "__main__":
    # Serve static files.
    app.mount(
        "/",
        StaticFiles(
            directory=cfg["fastapi_server"]["static_dir"],
            html=True
        )
    )
    # Run main application.
    asyncio.run(serve(app, app_config))