import threading
import time
import uuid
from botasaurus.browser import Driver, Wait
from config import logger, settings
from schemas import BrowserConfig, Element


class ElementCache:
    def __init__(self):
        self._cache = {}  # uuid -> {element, selector}
        self._lock = threading.Lock()  # Thread-safe access to cache

    def store(self, selector, element) -> str:
        """Store element and return UUID"""
        if element is None:
            # logger.error(f"Element is None for selector {selector}")
            return None

        element_uuid = str(uuid.uuid4())
        with self._lock:
            self._cache[element_uuid] = {"element": element, "selector": selector}
        return element_uuid

    def get(self, element_uuid: str):
        with self._lock:
            data = self._cache.get(element_uuid)
        return data["element"] if data else None


class BotasaurusBrowser:
    """Enhanced browser automation mixin with comprehensive error handling"""

    def __init__(self, config: BrowserConfig = BrowserConfig()):
        try:
            self._cache = ElementCache()
            self.config = config

            self.driver = Driver(
                headless=not settings.LOCAL_DEV,
            )

            self.is_initialized = True
        except Exception:
            self.is_initialized = False
            raise

    def _get_element(
        self, selector=None, element_id=None, timeout=None, multiple=False
    ):
        """Unified element retrieval"""
        logger.debug(
            f"_get_element called: selector={selector}, element_id={element_id}, timeout={timeout}, multiple={multiple}"
        )

        if selector and element_id:
            parent = self._cache.get(element_id)
            if not parent:
                logger.error(
                    f"Parent element not found in cache: element_id={element_id}"
                )
                return None
            logger.debug(
                f"Finding child element: selector={selector} within parent={element_id}"
            )
            return self._find_element(selector, timeout, multiple, parent=parent)
        elif selector:
            res = self._find_element(selector, timeout, multiple)
            return res
        elif element_id:
            res = self._cache.get(element_id)
            if not res:
                logger.error(f"Element not found in cache: element_id={element_id}")
            return res

        logger.warning("_get_element called without selector or element_id")
        return None

    def _find_element(self, selector, timeout, multiple, parent=None):
        start_time = time.time()
        try:
            if not parent:
                parent = self.driver
            wait = timeout if timeout else Wait.SHORT

            logger.debug(
                f"Finding element: selector={selector}, timeout={timeout}, multiple={multiple}, parent={'driver' if parent == self.driver else 'cached_element'}"
            )

            if multiple:
                elements = parent.select_all(selector, wait=wait)
                elapsed = time.time() - start_time
                logger.info(
                    f"Found {len(elements) if elements else 0} elements with selector '{selector}' in {elapsed:.3f}s"
                )
                return elements

            if timeout:
                element = parent.wait_for_element(selector, timeout)
                elapsed = time.time() - start_time
                logger.info(
                    f"Found element with selector '{selector}' after waiting {elapsed:.3f}s"
                )
                return element

            element = parent.select(selector)
            elapsed = time.time() - start_time
            logger.debug(
                f"Selected element with selector '{selector}' in {elapsed:.3f}s"
            )
            return element
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Failed to find element after {elapsed:.3f}s: selector={selector}, timeout={timeout}, multiple={multiple}, error={type(e).__name__}: {str(e)}"
            )
            return None

    def goto_page(self, url: str, timeout: int = 15, page_to_be: bool = True) -> bool:
        start_time = time.time()
        try:
            logger.info(
                f"Navigating to URL: {url} (timeout={timeout}s, page_to_be={page_to_be})"
            )

            # Clear element cache on navigation - elements from previous page are invalid
            cache_size = len(self._cache._cache)
            if cache_size > 0:
                self._cache._cache.clear()
                logger.debug(f"Cleared {cache_size} cached elements before navigation")

            self.driver.get(url, wait=timeout)

            if page_to_be:
                result = self.driver.wait_for_page_to_be(url, wait=timeout)
                elapsed = time.time() - start_time
                logger.info(
                    f"Navigation {'succeeded' if result else 'failed'}: {url} in {elapsed:.3f}s"
                )
                return result
            else:
                elapsed = time.time() - start_time
                logger.info(
                    f"Navigation completed: {url} in {elapsed:.3f}s (no page verification)"
                )
                return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Navigation failed after {elapsed:.3f}s: url={url}, timeout={timeout}, error={type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            return False

    def find_element(
        self, selector=None, element_id=None, timeout=None, multiple=False
    ):
        try:
            logger.debug(
                f"find_element: selector={selector}, element_id={element_id}, timeout={timeout}, multiple={multiple}"
            )
            resp = self._get_element(selector, element_id, timeout, multiple)
            if not resp:
                logger.warning(
                    f"Element not found: selector={selector}, element_id={element_id}, timeout={timeout}"
                )
                return None

            if multiple:
                cached_elements = [
                    Element(id=self._cache.store(selector, el), selector=selector)
                    for el in resp
                ]
                logger.info(
                    f"Cached {len(cached_elements)} elements with selector '{selector}'"
                )
                return cached_elements

            cached_id = self._cache.store(selector, resp)
            logger.info(
                f"Cached element with selector '{selector}', cache_id={cached_id}"
            )
            return Element(id=cached_id, selector=selector)

        except Exception as e:
            logger.error(
                f"Exception in find_element: selector={selector}, element_id={element_id}, error={type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            return None

    def element_exists(self, selector=None, element_id=None, timeout=None) -> bool:
        try:
            if element_id:
                exists = element_id in self._cache._cache
                logger.debug(
                    f"Checking element_id in cache: {element_id} - {'exists' if exists else 'not found'}"
                )
                return exists
            result = bool(self.find_element(selector, timeout=timeout))
            logger.debug(f"Element exists check: selector={selector}, result={result}")
            return result
        except Exception as e:
            logger.error(
                f"Exception in element_exists: selector={selector}, element_id={element_id}, error={type(e).__name__}: {str(e)}"
            )
            return False

    def wait_for_page(self, url, timeout=None) -> bool:
        start_time = time.time()
        try:
            logger.info(f"Waiting for page: url={url}, timeout={timeout}")
            (
                self.driver.wait_for_page_to_be(url, wait=timeout)
                if timeout
                else self.driver.wait_for_page_to_be(url)
            )
            elapsed = time.time() - start_time
            logger.info(f"Page ready: {url} after {elapsed:.3f}s")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Failed to wait for page after {elapsed:.3f}s: url={url}, timeout={timeout}, error={type(e).__name__}: {str(e)}"
            )
            return False

    def get_attribute(self, attribute, selector=None, element_id=None, timeout=None):
        try:
            logger.debug(
                f"Getting attribute: attribute={attribute}, selector={selector}, element_id={element_id}"
            )
            el = self._get_element(selector, element_id, timeout)
            if not el:
                logger.warning(
                    f"Element not found for attribute retrieval: attribute={attribute}, selector={selector}, element_id={element_id}"
                )
                return None
            value = el.get_attribute(attribute)
            logger.debug(
                f"Attribute '{attribute}' = '{value}' (selector={selector}, element_id={element_id})"
            )
            return value
        except Exception as e:
            logger.error(
                f"Failed to get attribute: attribute={attribute}, selector={selector}, element_id={element_id}, error={type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            return None

    def text_content(
        self, selector=None, element_id=None, wait=False, timeout=10
    ) -> str:
        try:
            logger.debug(
                f"Getting text content: selector={selector}, element_id={element_id}, wait={wait}, timeout={timeout}"
            )
            if element_id:
                el = self._cache.get(element_id)
                if not el:
                    logger.warning(
                        f"Element not found in cache for text retrieval: element_id={element_id}"
                    )
                    return ""
                text = el.text
                logger.debug(
                    f"Text content retrieved from cached element: length={len(text)}, preview='{text[:50]}...'"
                )
                return text

            text = (
                self.driver.get_text(selector, wait=timeout)
                if wait
                else self.driver.get_text(selector)
            )
            logger.debug(
                f"Text content retrieved: selector={selector}, length={len(text)}, preview='{text[:50]}...'"
            )
            return text
        except Exception as e:
            logger.error(
                f"Failed to get text content: selector={selector}, element_id={element_id}, error={type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            return ""

    def fill_input(
        self, text, selector=None, element_id=None, timeout=None, clear=True
    ) -> bool:
        try:
            logger.info(
                f"Filling input: selector={selector}, element_id={element_id}, text_length={len(text)}, clear={clear}"
            )
            el = self._get_element(selector, element_id, timeout)
            if not el:
                logger.warning(
                    f"Element not found for input fill: selector={selector}, element_id={element_id}"
                )
                return False
            if clear:
                logger.debug("Clearing input field")
                el.clear()
            el.type(text)
            logger.info(
                f"Input filled successfully: selector={selector}, element_id={element_id}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to fill input: selector={selector}, element_id={element_id}, error={type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            return False

    def click(self, selector=None, element_id=None, timeout=None) -> bool:
        try:
            logger.info(
                f"Clicking element: selector={selector}, element_id={element_id}, timeout={timeout}"
            )
            el = self._get_element(selector, element_id, timeout)
            if not el:
                logger.warning(
                    f"Element not found for click: selector={selector}, element_id={element_id}"
                )
                return False
            el.click()
            logger.info(
                f"Click successful: selector={selector}, element_id={element_id}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to click: selector={selector}, element_id={element_id}, error={type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            return False


    def close(self):
        try:
            if hasattr(self, "driver"):
                logger.info("Closing browser driver")
                self.driver.close()
                logger.info("Browser driver closed successfully")
            else:
                logger.warning("No driver attribute found during close")
        except Exception as e:
            logger.error(
                f"Error closing browser driver: error={type(e).__name__}: {str(e)}",
                exc_info=True,
            )
