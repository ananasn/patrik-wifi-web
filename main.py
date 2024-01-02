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
    print(credintals.password, credintals.ssid)
    return credintals


@app.get("/ssid/")
async def scan_ssid() -> list[SSID]:
    iwlist_raw = Popen(["iwlist", "scan"], stdout=PIPE)
    ap_list, err = iwlist_raw.communicate()
    ap_array = []

    for line in ap_list.decode("utf-8").rsplit("\n"):
        iwlist_raw = Popen(["nmcli", "dev", "wifi"], stdout=PIPE)
        ap_list, _ = iwlist_raw.communicate()
        ap_array = []

        for line in ap_list.decode("utf-8").rsplit("\n")[1:]:  # Skip table title.
            # Skip leading asteriks (*) -- current network mark, get SSID
            if line:
                ap_ssid = line[1:].split()[1]
                if ap_ssid not in ("", "--"):
                    ap_array.append(SSID(text=ap_ssid))

    return ap_array


app.mount("/", StaticFiles(directory="static/dist", html=True))


if __name__ == "__main__":
    nmcli = Popen(["nmcli", "dev", "wifi", "connect", "catnet", "password", "123456789"], stdout=PIPE)
    answer, err = nmcli.communicate()
    if answer.startswith("Error"):
        print("NYA")
    print(answer, err)
