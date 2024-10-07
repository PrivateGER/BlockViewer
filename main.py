import threading
from fastapi import FastAPI, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
import requests
from fastapi import BackgroundTasks
import time
import jinja2

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

META_URL = "https://plasmatrap.com/api/admin/meta"
TOKEN = ""
blocks_data = {"reject": [], "followers_only": []}

def update_blocks():
    global blocks_data
    try:
        response = requests.post(META_URL, json={"i": TOKEN})
        data = response.json()

        if not data:
            raise Exception("No data received from the server.")


        print("Refreshed block data.")

        blocks_data["reject"] = data.get('blockedHosts', [])
        blocks_data["followers_only"] = data.get('silencedHosts', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "updated", "reject_count": len(blocks_data["reject"]), "followers_only_count": len(blocks_data["followers_only"])}


def fetch_blocks_regularly():
    update_blocks()
    while True:
        time.sleep(3600)  # every hour
        try:
            update_blocks()
        except:
            pass

@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=fetch_blocks_regularly, daemon=True)
    thread.start()

@app.get("/")
def read_blocks(request: Request):
    return templates.TemplateResponse("blocks.html", {"request": request, "blocks": blocks_data})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
