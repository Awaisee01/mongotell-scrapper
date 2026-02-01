from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import CallHistory, VoicemailScraper, ChatSmsScraper
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

@app.get("/voicemails")
def run_voicemail_scraper():
    print("Starting Voicemail Scraper...")
    try:
        bot = VoicemailScraper()
        json_data = bot.scrape()
        
        # Parse json to count results (optional, for logging)
        data = json.loads(json_data)
        count = data.get("count", 0)
        print(f"✅ Voicemail Scraper finished successfully. Found {count} records.")
        return data
    except Exception as e:
        error_details = traceback.format_exc()
        print("❌ Voicemail Scraper Error:", error_details)
        return {"status": "error", "message": str(e), "details": error_details}

@app.get("/messages")
def run_messages_scraper():
    print("Starting Chat & SMS Scraper...")
    try:
        bot = ChatSmsScraper()
        json_data = bot.scrape()
        
        # Parse json to count results
        data = json.loads(json_data)
        count = data.get("count", 0)
        print(f"✅ Users Scraper finished successfully. Found {count} messages.")
        return data
    except Exception as e:
        error_details = traceback.format_exc()
        print("❌ Messages Scraper Error:", error_details)
        return {"status": "error", "message": str(e), "details": error_details}
