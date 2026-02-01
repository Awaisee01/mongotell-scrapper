import cloudinary

from base import BotasaurusBrowser
from datetime import datetime
import json
from config import logger, settings
from utils import download_with_browser_session, upload_to_cloudinary

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

class CallHistory(BotasaurusBrowser):
    USERNAME = settings.MONGOTEL_USERNAME
    PASSWORD = settings.MONGOTEL_PASSWORD
    BASE_URL = "https://portal.mongotel.com/portal/login/"

    def scrape(self, limit=50):
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

            all_results = []
            
            # Wait for initial data load
            logger.info("Waiting for table data to load...")
            self.element_exists("#call-history-table tbody tr", timeout=20)

            while True:
                rows = self.find_element("#call-history-table tbody tr", multiple=True) or []
                
                # Retry once if rows are empty despite wait
                if not rows:
                    logger.info("No rows found, waiting a bit more...")
                    self.sleep(5)
                    rows = self.find_element("#call-history-table tbody tr", multiple=True) or []

                logger.info(f"Processing {len(rows)} rows...")

                results = []
                for row in rows:
                    try:
                        # Helper to find text within the current row
                        def get_text_from_row(selector):
                            el = self.find_element(selector, element_id=row.id)
                            return self.text_content(element_id=el.id).strip() if el else None

                        # Helper to get attribute within the current row
                        def get_attr_from_row(selector, attr):
                            el = self.find_element(selector, element_id=row.id)
                            return self.get_attribute(attr, element_id=el.id) if el else None

                        # Extract data relative to the ROW context
                        from_name = get_text_from_row(".from_name-field")
                        from_number = get_text_from_row(".from-field a") # Looking for <a> specifically
                        
                        # If <a> not found, try text directly in .from-field (fallback)
                        if not from_number:
                            from_number = get_text_from_row(".from-field")

                        to_field = get_text_from_row(".to-field")
                        dialed_number = get_text_from_row(".dialed-field a") or get_text_from_row(".dialed-field")
                        date_val = get_text_from_row(".date-field")
                        duration = get_text_from_row(".duration-field")
                        release_reason = get_text_from_row(".release_reason-field")

                        # QoS Links (Expect 2 per row usually, or specific structure)
                        # Note: QoS structure might be tricky if it relies on index. 
                        # Assuming .view-qos exists inside the row.
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

                        results.append({
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
                        })

                    except Exception as e:
                        logger.error(f"Row skipped due to error: {e}")
                
                all_results.extend(results)
                
                if len(all_results) >= limit:
                    logger.info(f"Limit of {limit} reached. Stopping.")
                    all_results = all_results[:limit]
                    break

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
        finally:
            if hasattr(self, 'driver'):
                self.driver.close()

        return json.dumps({
            "scraped_at": datetime.now().isoformat(),
            "results": all_results
        }, indent=4, ensure_ascii=False)



class VoicemailScraper(BotasaurusBrowser):
    USERNAME = settings.MONGOTEL_USERNAME
    PASSWORD = settings.MONGOTEL_PASSWORD
    BASE_URL = "https://portal.mongotel.com/portal/login/"
    VOICEMAILS_URL = "https://portal.mongotel.com/portal/voicemails"

    def scrape(self):
        try:
            self.driver.get(self.BASE_URL)
            
            # Check if login is needed (using selectors from CallHistory)
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
            results = []

            logger.info(f"Found {len(rows)} potential rows, extracting data...")

            for row in rows:
                try:
                    # 1. Check for expected column count (Based on user HTML: exactly 6 columns)
                    cols = self.find_element("td", element_id=row.id, multiple=True)
                    
                    if not cols or len(cols) != 6:
                        # logger.debug(f"Skipping row with {len(cols) if cols else 0} columns (expected 6)")
                        continue

                    # 2. Extract Data
                    # Col 0: Audio Player (skip)
                    
                    # Col 1: Number (text content of the cell or the link inside)
                    number = self.text_content(element_id=cols[1].id).strip()
                    
                    # Col 2: Name
                    name = self.text_content(element_id=cols[2].id).strip()

                    # Col 3: Date
                    date_val = self.text_content(element_id=cols[3].id).strip()

                    # Col 4: Duration
                    duration = self.text_content(element_id=cols[4].id).strip()

                    # Col 5: Actions (contains download link .download-audio)
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

                    results.append({
                        "name": name,
                        "number": number,
                        "date": date_val,
                        "duration": duration,
                        "audio": {
                            "portal_url": audio_url,
                            "cloudinary_url": audio_cloud_url
                        }
                    })

                    if len(results) >= limit:
                        break

                except Exception as e:
                    logger.error(f"Voicemail row skipped due to error: {e}")

            logger.info(f"Successfully scraped {len(results)} voicemails.")
            
            return json.dumps({
                "scraped_at": datetime.now().isoformat(),
                "count": len(results),
                "results": results
            }, indent=4, ensure_ascii=False)
        finally:
            if hasattr(self, 'driver'):
                self.driver.close()


class ChatSmsScraper(BotasaurusBrowser):
    USERNAME = settings.MONGOTEL_USERNAME
    PASSWORD = settings.MONGOTEL_PASSWORD
    BASE_URL = "https://portal.mongotel.com/portal/login/"
    MESSAGES_URL = "https://portal.mongotel.com/portal/messages"

    def scrape(self):
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
            results = []

            logger.info(f"Found {len(rows)} potential rows, extracting data...")

            for row in rows:
                try:
                    cols = self.find_element("td", element_id=row.id, multiple=True)
                    
                    # We expect at least 5-6 columns based on the HTML
                    if not cols or len(cols) < 5:
                        continue

                    # Col 1: Number (text content of the cell or the link inside)
                    # Note: Using safe access
                    number = self.text_content(element_id=cols[1].id).strip()
                    
                    # Col 3: Message
                    message = self.text_content(element_id=cols[3].id).strip()
                    
                    # Col 4: Time
                    time_val = self.text_content(element_id=cols[4].id).strip()
                    
                    if number or message:
                        results.append({
                            "number": number,
                            "message": message,
                            "time": time_val
                        })
                    
                    if len(results) >= limit:
                        break

                except Exception as e:
                    logger.error(f"Message row skipped due to error: {e}")

            logger.info(f"Successfully scraped {len(results)} messages.")
            
            return json.dumps({
                "scraped_at": datetime.now().isoformat(),
                "count": len(results),
                "results": results
            }, indent=4, ensure_ascii=False)
        finally:
            if hasattr(self, 'driver'):
                self.driver.close()


if __name__ == "__main__":
    # bot = CallHistory()
    # bot = VoicemailScraper()
    bot = ChatSmsScraper()
    data = bot.scrape()
    print(data)
