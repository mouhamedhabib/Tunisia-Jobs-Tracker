import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# Logging setup - prints messages with time, level, and text
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class BaseScraper:
    """
    Base class for all scrapers.
    Every scraper (emploi_tn, keejob...) inherits from this class.
    """

    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.delay = int(os.getenv("REQUEST_DELAY", 2))
        self.max_pages = int(os.getenv("MAX_PAGES", 10))
        self.session = requests.Session()

        # Pretend to be a real browser
        self.session.headers.update({
            "User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0"),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def get_page(self, url: str) -> BeautifulSoup | None:
        """
        Fetch a URL and return a BeautifulSoup object.
        Returns None if request fails.
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Raises error if status is 4xx or 5xx
            time.sleep(self.delay)       # Wait between requests
            return BeautifulSoup(response.text, "lxml")

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            return None

        except requests.exceptions.ConnectionError:
            logger.error(f"Connection failed for {url}")
            return None

        except requests.exceptions.Timeout:
            logger.error(f"Timeout for {url}")
            return None

    def scrape(self) -> list[dict]:
        """
        Main method - must be implemented by each scraper.
        Raises error if child class does not implement it.
        """
        raise NotImplementedError(f"{self.source_name} must implement scrape()")

    def run(self) -> list[dict]:
        """Run the scraper and return results with basic stats."""
        logger.info(f"Starting scraper: {self.source_name}")
        jobs = self.scrape()
        logger.info(f"Finished: {len(jobs)} jobs found from {self.source_name}")
        return jobs
