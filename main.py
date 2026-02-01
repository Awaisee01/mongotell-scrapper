from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import CallHistory, VoicemailScraper, ChatSmsScraper
import json
import threading
import traceback

app = FastAPI()

# Global lock to prevent multiple scrapers from running simultaneously (OOM protection)
scraper_lock = threading.Lock()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "mongotel_scraper"}

@app.get("/call_history")
def run_scraper():
    # Attempt to acquire lock without blocking
    if not scraper_lock.acquire(blocking=False):
        print("⚠️ Request rejected: Server busy with another scrape task")
        return {"status": "error", "message": "Server is busy with another scraping task. Please try again in 30 seconds."}
    
    try:
        print("🔒 Lock acquired, starting Call History Scraper...")
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
    finally:
        scraper_lock.release()
        print("🔓 Lock released")

@app.get("/voicemails")
def run_voicemail_scraper():
    if not scraper_lock.acquire(blocking=False):
        print("⚠️ Request rejected: Server busy with another scrape task")
        return {"status": "error", "message": "Server is busy with another scraping task. Please try again in 30 seconds."}

    try:
        print("🔒 Lock acquired, starting Voicemail Scraper...")
        bot = VoicemailScraper()
        json_data = bot.scrape()
        
        data = json.loads(json_data)
        count = data.get("count", 0)
        print(f"✅ Voicemail Scraper finished successfully. Found {count} records.")
        return data
    except Exception as e:
        error_details = traceback.format_exc()
        print("❌ Voicemail Scraper Error:", error_details)
        return {"status": "error", "message": str(e), "details": error_details}
    finally:
        scraper_lock.release()
        print("🔓 Lock released")

@app.get("/messages")
def run_messages_scraper():
    if not scraper_lock.acquire(blocking=False):
        print("⚠️ Request rejected: Server busy with another scrape task")
        return {"status": "error", "message": "Server is busy with another scraping task. Please try again in 30 seconds."}

    try:
        print("🔒 Lock acquired, starting Chat & SMS Scraper...")
        bot = ChatSmsScraper()
        json_data = bot.scrape()
        
        data = json.loads(json_data)
        count = data.get("count", 0)
        print(f"✅ Messages Scraper finished successfully. Found {count} messages.")
        return data
    except Exception as e:
        error_details = traceback.format_exc()
        print("❌ Messages Scraper Error:", error_details)
        return {"status": "error", "message": str(e), "details": error_details}
    finally:
        scraper_lock.release()
        print("🔓 Lock released")
