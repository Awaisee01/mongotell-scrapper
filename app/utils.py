import requests
import cloudinary
import cloudinary.uploader
from uuid import uuid4

def download_with_browser_session(driver, url):
    session = requests.Session()

    # copy cookies from browser
    for c in driver.get_cookies():
        session.cookies.set(c["name"], c["value"])

    r = session.get(url, timeout=60)
    r.raise_for_status()
    return r.content



def upload_to_cloudinary(audio_bytes):
    public_id = f"calls/{uuid4()}"
    result = cloudinary.uploader.upload(
        audio_bytes,
        resource_type="video",
        public_id=public_id,
        format="mp3"
    )

    return result["secure_url"]
