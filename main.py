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

BLOCKS_URL = "https://fba.ryona.agency/api?reverse=plasmatrap.com"
blocks_data = {"reject": [], "followers_only": []}

@app.get("/update_blocks/")
def update_blocks():
    global blocks_data
    try:
        response = requests.get(BLOCKS_URL)
        data = response.json()

        # FBA is not really a trusted source. We should check if the data is valid, if it doesn't contain pawoo and bae.st we're being fed nonsense.
        # Iterate over the data and check if it contains pawoo and bae.st
        canaryDomains = [
            {
                "domain": "pawoo.net",
                "found": False
            },
            {
                "domain": "bae.st",
                "found": False
            }
        ]

        for domain in canaryDomains:
            for block in data.get('reject', []):
                if domain["domain"] == block["blocked"]:
                    print("Canary domain found, marking...")
                    domain["found"] = True

        # If the canary domains are not found, we're being fed nonsense. Raise an exception.
        for domain in canaryDomains:
            if not domain["found"]:
                raise Exception("Canary domain not found, data is invalid.")

        print("Refreshed block data.")

        blocks_data["reject"] = data.get('reject', [])
        blocks_data["followers_only"] = data.get('followers_only', [])
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
