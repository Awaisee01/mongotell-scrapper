import time
import json
from datetime import datetime
from base import BotasaurusBrowser, logger
from botasaurus.browser import Driver, Wait
from selenium.webdriver.common.by import By
from config import settings
from utils import download_with_browser_session, upload_to_cloudinary

class CallHistory(BotasaurusBrowser):
    USERNAME = settings.MONGOTEL_USERNAME
    PASSWORD = settings.MONGOTEL_PASSWORD
    BASE_URL = "https://portal.mongotel.com/portal/login/"

    def scrape_generator(self, limit=50):
        try:
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

            # Wait for initial data load
            logger.info("Waiting for table data to load...")
            self.element_exists("#call-history-table tbody tr", timeout=20)
            
            count = 0

            while True:
                rows = self.find_element("#call-history-table tbody tr", multiple=True) or []
                
                # Retry once if rows are empty despite wait
                if not rows:
                    logger.info("No rows found, waiting a bit more...")
                    self.sleep(5)
                    rows = self.find_element("#call-history-table tbody tr", multiple=True) or []

                logger.info(f"Processing {len(rows)} rows...")

                for row in rows:
                    if count >= limit:
                        logger.info(f"Limit of {limit} reached.")
                        return

                    try:
                        # Helper to find text within the current row
                        def get_text_from_row(selector):
                            el = self.find_element(selector, element_id=row.id)
                            return self.text_content(element_id=el.id).strip() if el else None

                        # Extract data relative to the ROW context
                        from_name = get_text_from_row(".from_name-field")
                        from_number = get_text_from_row(".from-field a")
                        if not from_number:
                            from_number = get_text_from_row(".from-field")

                        to_field = get_text_from_row(".to-field")
                        dialed_number = get_text_from_row(".dialed-field a") or get_text_from_row(".dialed-field")
                        date_val = get_text_from_row(".date-field")
                        duration = get_text_from_row(".duration-field")
                        release_reason = get_text_from_row(".release_reason-field")

                        # QoS Links
                        qos_links = self.find_element("a.view-qos", element_id=row.id, multiple=True) or []
                        qos_in = self.text_content(element_id=qos_links[0].id).strip() if len(qos_links) > 0 else None
                        qos_out = self.text_content(element_id=qos_links[1].id).strip() if len(qos_links) > 1 else None

                        # Audio
                        audio_url = None
                        audio_cloud_url = None
                        
                        audio_el = self.find_element("a.download-audio", element_id=row.id)
                        if audio_el:
                             cls = self.get_attribute("class", element_id=audio_el.id)
                             if cls and "disabled" not in cls:
                                 audio_url = self.get_attribute("href", element_id=audio_el.id)

                        if audio_url:
                            try:
                                audio_bytes = download_with_browser_session(self.driver, url=audio_url)
                                audio_cloud_url = upload_to_cloudinary(audio_bytes)
                            except Exception as e:
                                logger.error(f"Audio upload failed for row: {e}")

                        record = {
                            "from": {
                                "name": from_name,
                                "number": from_number,
                            },
                            "to": to_field,
                            "dialed_number": dialed_number,
                            "date": date_val,
                            "duration": duration,
                            "release_reason": release_reason,
                            "qos": {
                                "inbound": qos_in,
                                "outbound": qos_out,
                            },
                            "audio": {
                                "portal_url": audio_url,
                                "cloudinary_url": audio_cloud_url
                            }
                        }
                        
                        yield record
                        count += 1

                    except Exception as e:
                        logger.error(f"Row skipped due to error: {e}")
                
                #  Check if "Next" is disabled
                next_button = self.find_element("li.next", multiple=False)
                if not next_button:
                    break
                cls = self.get_attribute("class", element_id=next_button.id)
                if "disabled" in cls:
                    break
                else:
                    # Click Next
                    link = next_button.find_element_by_tag_name("a")
                    if link:
                        self.click(link)
                        self.wait_for_page(link)
                    else:
                        break
        finally:
            if hasattr(self, 'driver'):
                self.driver.close()


class VoicemailScraper(BotasaurusBrowser):
    USERNAME = settings.MONGOTEL_USERNAME
    PASSWORD = settings.MONGOTEL_PASSWORD
    BASE_URL = "https://portal.mongotel.com/portal/login/"
    VOICEMAILS_URL = "https://portal.mongotel.com/portal/voicemails"

    def scrape_generator(self, limit=50):
        try:
            self.driver.get(self.BASE_URL)
            
            # Check if login is needed
            if self.element_exists("#LoginUsername", timeout=5):
                logger.info("Logging in...")
                self.fill_input(selector="#LoginUsername", text=self.USERNAME)
                self.fill_input(selector="#LoginPassword", text=self.PASSWORD)
                self.click('input[type="submit"][value="Log In"]')
                self.element_exists("#navbar-mobile", timeout=10)
            
            logger.info("Navigating to Voicemails...")
            self.goto_page(self.VOICEMAILS_URL)
            
            # Wait for table
            self.element_exists("table tbody tr", timeout=15)
            
            rows = self.find_element("table tbody tr", multiple=True) or []
            logger.info(f"Found {len(rows)} potential rows, extracting data...")
            
            count = 0
            for row in rows:
                if count >= limit:
                    logger.info(f"Limit of {limit} reached.")
                    return

                try:
                    cols = self.find_element("td", element_id=row.id, multiple=True)
                    if not cols or len(cols) != 6:
                        continue

                    number = self.text_content(element_id=cols[1].id).strip()
                    name = self.text_content(element_id=cols[2].id).strip()
                    date_val = self.text_content(element_id=cols[3].id).strip()
                    duration = self.text_content(element_id=cols[4].id).strip()

                    audio_url = None
                    audio_cloud_url = None
                    audio_el = self.find_element(".download-audio", element_id=cols[5].id)
                    if audio_el:
                        audio_url = self.get_attribute("href", element_id=audio_el.id)

                    if audio_url:
                        try:
                            audio_bytes = download_with_browser_session(self.driver, url=audio_url)
                            audio_cloud_url = upload_to_cloudinary(audio_bytes)
                        except Exception as e:
                            logger.error(f"Audio upload failed for voicemail from {number}: {e}")

                    yield {
                        "name": name,
                        "number": number,
                        "date": date_val,
                        "duration": duration,
                        "audio": {
                            "portal_url": audio_url,
                            "cloudinary_url": audio_cloud_url
                        }
                    }
                    count += 1

                except Exception as e:
                    logger.error(f"Voicemail row skipped due to error: {e}")

        finally:
            if hasattr(self, 'driver'):
                self.driver.close()


class ChatSmsScraper(BotasaurusBrowser):
    USERNAME = settings.MONGOTEL_USERNAME
    PASSWORD = settings.MONGOTEL_PASSWORD
    BASE_URL = "https://portal.mongotel.com/portal/login/"
    MESSAGES_URL = "https://portal.mongotel.com/portal/messages"

    def scrape_generator(self, limit=50):
        try:
            self.driver.get(self.BASE_URL)
            
            # Check if login is needed
            if self.element_exists("#LoginUsername", timeout=5):
                logger.info("Logging in...")
                self.fill_input(selector="#LoginUsername", text=self.USERNAME)
                self.fill_input(selector="#LoginPassword", text=self.PASSWORD)
                self.click('input[type="submit"][value="Log In"]')
                self.element_exists("#navbar-mobile", timeout=10)
            
            logger.info("Navigating to Messages...")
            self.goto_page(self.MESSAGES_URL)
            
            # Wait for table
            self.element_exists("table tbody tr", timeout=15)
            
            rows = self.find_element("table tbody tr", multiple=True) or []
            logger.info(f"Found {len(rows)} potential rows, extracting data...")

            count = 0
            for row in rows:
                if count >= limit:
                    logger.info(f"Limit of {limit} reached.")
                    return

                try:
                    cols = self.find_element("td", element_id=row.id, multiple=True)
                    if not cols or len(cols) < 5:
                        continue

                    number = self.text_content(element_id=cols[1].id).strip()
                    message = self.text_content(element_id=cols[3].id).strip()
                    time_val = self.text_content(element_id=cols[4].id).strip()
                    
                    if number or message:
                        yield {
                            "number": number,
                            "message": message,
                            "time": time_val
                        }
                        count += 1

                except Exception as e:
                    logger.error(f"Message row skipped due to error: {e}")

        finally:
            if hasattr(self, 'driver'):
                self.driver.close()


if __name__ == "__main__":
    # Test generator
    bot = ChatSmsScraper()
    for item in bot.scrape_generator(limit=5):
        print(item)
