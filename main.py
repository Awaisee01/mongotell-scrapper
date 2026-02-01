from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import CallHistory
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "mongotel_scraper"}


import traceback

@app.get("/call_history")
def run_scraper():
    try:
        bot = CallHistory()
        data = bot.scrape()
        parsed_data = json.loads(data)
        count = len(parsed_data.get("results", []))
        print(f"✅ Scraper finished successfully. Returning {count} records.")
        return parsed_data
    except Exception as e:
        error_details = traceback.format_exc()
        print("❌ Scraper Error:", error_details)
        return {"status": "error", "message": str(e), "details": error_details}
