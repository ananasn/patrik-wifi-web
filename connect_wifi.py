import os
import sys
import asyncio
import logging
# import webbrowser

from uuid import UUID, uuid4
from logging.handlers import RotatingFileHandler
from subprocess import Popen, PIPE

from hypercorn.asyncio import serve
from hypercorn.config import Config
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

 
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
    answer, err = nmcli.communicate()
    if err and err.split()[0] == b"Error:":
        msg = f"Не удалось подключиться к сети {credintals.ssid}"

        if answer:
            logging.info(answer)
        logging.error(msg)
        logging.error(err)

        return {"message": msg}
    
    url = sys.argv[1]
    if url:
        logging.info(f"Openning url: {url}")
        # webbrowser.get(using='chromium-browser').open_new_tab(url)
        Popen(
            [f"sh start-browser.sh {url}"],
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
    # Serve static files
    app.mount("/", StaticFiles(directory="static/dist", html=True))
    # Run main application
    asyncio.run(serve(app, config))