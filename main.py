from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from scraper import CallHistory, VoicemailScraper, ChatSmsScraper
import json
import threading
import traceback
import time

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

def stream_generator(bot_class, limit):
    """
    Generator wrapper that handles locking and conversion to NDJSON.
    """
    # Attempt to acquire lock
    if not scraper_lock.acquire(blocking=False):
        yield json.dumps({"status": "error", "message": "Server is busy. Please try again later."}) + "\n"
        return

    try:
        print(f"🔒 Lock acquired for {bot_class.__name__} (Limit: {limit})")
        bot = bot_class()
        # Yield metadata first (optional, but helpful for client initialization)
        yield json.dumps({"type": "meta", "status": "started", "limit": limit}) + "\n"
        
        count = 0
        for record in bot.scrape_generator(limit=limit):
            yield json.dumps({"type": "data", "record": record}) + "\n"
            count += 1
        
        yield json.dumps({"type": "meta", "status": "completed", "count": count}) + "\n"
        print(f"✅ Stream finished. Sent {count} records.")

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"❌ Stream Error: {e}")
        yield json.dumps({"type": "error", "message": str(e), "details": error_details}) + "\n"
    finally:
        scraper_lock.release()
        print("🔓 Lock released")

@app.get("/call_history")
def stream_call_history(limit: int = 50):
    return StreamingResponse(
        stream_generator(CallHistory, limit),
        media_type="application/x-ndjson"
    )

@app.get("/voicemails")
def stream_voicemails(limit: int = 50):
    return StreamingResponse(
        stream_generator(VoicemailScraper, limit),
        media_type="application/x-ndjson"
    )

@app.get("/messages")
def stream_messages(limit: int = 50):
    return StreamingResponse(
        stream_generator(ChatSmsScraper, limit),
        media_type="application/x-ndjson"
    )
