from fastapi import FastAPI
from .scraper import CallHistory
import json

app = FastAPI()


@app.get("/call_history")
def run_scraper():
    try:
        bot = CallHistory()
        data = bot.scrape()
        return json.loads(data)
    except Exception as e:
        return {"status": "error", "message": str(e)}
