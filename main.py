import webbrowser

from subprocess import Popen, PIPE
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

 
app = FastAPI()

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
        return {
            "message": f"Не удалось подключиться к сети {credintals.ssid}"
        }
    webbrowser.open_new_tab("ya.ru")
    return {
        "message": f"Подключено к сети {credintals.ssid}"}


@app.get("/ssid/")
async def scan_ssid() -> list[SSID]:
    iwlist_raw = Popen(
        ["nmcli -t -f active,ssid dev wifi"],
        shell=True,
        stdout=PIPE
    )
    ap_list, _ = iwlist_raw.communicate()
    ap_array = []

    for line in ap_list.decode("utf-8").rsplit("\n"):
        try:
            _, ap_ssid = line.split(":")
            if ap_ssid:
                ap_array.append(SSID(text=ap_ssid))
        except ValueError:
            continue
    
    return ap_array


app.mount("/", StaticFiles(directory="static/dist", html=True))
