import cloudinary

from .base import BotasaurusBrowser
from datetime import datetime
import json
from .config import logger
from .utils import download_with_browser_session, upload_to_cloudinary

cloudinary.config(
    cloud_name="dvaxklnue",
    api_key="915578838771632",
    api_secret="HvqKuSZLNy5OS_LgYn7ka4YTIsg",
    secure=True
)

class CallHistory(BotasaurusBrowser):
    USERNAME = "100@wfw"
    PASSWORD = "Wolf@5136"
    BASE_URL = "https://portal.mongotel.com/portal/login/"

    def scrape(self):
        if not self.USERNAME or not self.PASSWORD:
            raise ValueError("Missing credentials")

        self.goto_page(self.BASE_URL)
        self.fill_input(selector="#LoginUsername", text=self.USERNAME, timeout=10)
        self.fill_input(selector="#LoginPassword", text=self.PASSWORD)
        self.click('input[type="submit"][value="Log In"]')

        self.element_exists("#LinkCallhistoryIndex", timeout=15)
        self.click("#LinkCallhistoryIndex")

        # Set table columns
        self.click("#table-column-selector-title", timeout=10)
        self.click('input[data-table="callhistory"][value="qos"]')
        self.click('input[data-table="callhistory"][value="release_reason"]')
        self.click('#call-history-table')

        all_results = []

        while True:
            rows = self.find_element("#call-history-table tbody tr", multiple=True) or []

            from_names = self.find_element(".from_name-field", multiple=True) or []
            from_numbers = self.find_element(".from-field a", multiple=True) or []
            dialed_numbers = self.find_element(".dialed-field a", multiple=True) or []
            tos = self.find_element(".to-field", multiple=True) or []
            dates = self.find_element(".date-field", multiple=True) or []
            durations = self.find_element(".duration-field", multiple=True) or []
            release_reasons = self.find_element(".release_reason-field", multiple=True) or []
            qos_links = self.find_element("a.view-qos", multiple=True) or []
            audio_links = self.find_element("a.download-audio", multiple=True) or []

            def safe_text(el):
                return self.text_content(element_id=el.id).strip() if el else None

            results = []

            for i in range(len(rows)):
                try:
                    qos_in = qos_links[i * 2] if len(qos_links) > i * 2 else None
                    qos_out = qos_links[i * 2 + 1] if len(qos_links) > i * 2 + 1 else None

                    # AUDIO
                    audio_url = None
                    audio_cloud_url = None

                    if i < len(audio_links):
                        el = audio_links[i]
                        cls = self.get_attribute("class", element_id=el.id)
                        if cls and "disabled" not in cls:
                            audio_url = self.get_attribute("href", element_id=el.id)

                    if audio_url:
                        try:
                            audio_bytes = download_with_browser_session(self.driver, url=audio_url)
                            audio_cloud_url = upload_to_cloudinary(audio_bytes)
                        except Exception as e:
                            logger.error(f"Audio upload failed for row {i}: {e}")

                    results.append({
                        "from": {
                            "name": safe_text(from_names[i]) if i < len(from_names) else None,
                            "number": safe_text(from_numbers[i]) if i < len(from_numbers) else None,
                        },
                        "to": safe_text(tos[i]) if i < len(tos) else None,
                        "dialed_number": safe_text(dialed_numbers[i]) if i < len(dialed_numbers) else None,
                        "date": safe_text(dates[i]) if i < len(dates) else None,
                        "duration": safe_text(durations[i]) if i < len(durations) else None,
                        "release_reason": safe_text(release_reasons[i]) if i < len(release_reasons) else None,
                        "qos": {
                            "inbound": safe_text(qos_in),
                            "outbound": safe_text(qos_out),
                        },
                        "audio": {
                            "portal_url": audio_url,
                            "cloudinary_url": audio_cloud_url
                        }
                    })

                except Exception as e:
                    logger.error(f"Row {i} skipped: {e}")

            all_results.extend(results)

            #  Check if "Next" is disabled
            next_button = self.find_element("li.next", multiple=False)
            if not next_button:
                break  # No pagination
            cls = self.get_attribute("class", element_id=next_button.id)
            if "disabled" in cls:
                break  # Reached last page
            else:
                # Click Next
                link = next_button.find_element_by_tag_name("a")
                if link:
                    self.click(link)
                    self.wait_for_page(link)
                else:
                    break

        self.driver.close()

        return json.dumps({
            "scraped_at": datetime.now().isoformat(),
            "results": all_results
        }, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    bot = CallHistory()
    data = bot.scrape()
    print(data)
