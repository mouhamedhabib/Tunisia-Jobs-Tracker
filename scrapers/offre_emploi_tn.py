from scrapers.base_scraper import BaseScraper
from database.db import insert_job
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://www.offre-emploi.tn"
JOBS_URL = f"{BASE_URL}/offres-emploi/page/"


class OffreEmploiTnScraper(BaseScraper):
    """Scraper for offre-emploi.tn"""

    def __init__(self):
        super().__init__(
            source_name="offre_emploi_tn",
            base_url=BASE_URL
        )

    def parse_job(self, article) -> dict | None:
        """Extract job data from one article.js_result_row element."""
        try:
            # Title and URL
            title_tag = article.select_one("div.jobTitle h2 a")
            if not title_tag:
                return None
            title = title_tag.get_text(strip=True)
            url = title_tag.get("href", "")

            # Location div has two links: sector | city
            location_links = article.select("div.location a")
            sector = location_links[0].get_text(strip=True) if len(location_links) > 0 else None
            city   = location_links[1].get_text(strip=True) if len(location_links) > 1 else None

            # Description / preview
            preview_tag = article.select_one("div.preview")
            description = preview_tag.get_text(strip=True) if preview_tag else None

            # Posted date
            time_tag = article.select_one("time")
            posted_at = time_tag.get_text(strip=True) if time_tag else None

            return {
                "title":     title,
                "company":   None,   # Not available in listing
                "city":      city,
                "region":    None,
                "contract":  None,   # Not available in listing
                "skills":    sector,
                "salary":    None,
                "source":    "offre_emploi_tn",
                "url":       url,
                "posted_at": posted_at,
            }

        except Exception as e:
            logger.error(f"Error parsing job: {e}")
            return None

    def scrape(self) -> list[dict]:
        """Scrape job listings page by page."""
        all_jobs = []

        for page_num in range(1, self.max_pages + 1):
            url = f"{JOBS_URL}{page_num}/"
            soup = self.get_page(url)

            if not soup:
                logger.warning(f"Failed to fetch page {page_num} - stopping")
                break

            articles = soup.select("article.js_result_row")

            # Filter out ad articles
            articles = [a for a in articles if a.select_one("div.jobTitle")]

            if not articles:
                logger.info(f"No jobs on page {page_num} - reached end")
                break

            logger.info(f"Page {page_num}: found {len(articles)} jobs")

            for article in articles:
                job = self.parse_job(article)
                if job:
                    inserted = insert_job(job)
                    if inserted:
                        all_jobs.append(job)
                        logger.info(f"Saved: {job['title']} @ {job['city']}")
                    else:
                        logger.info(f"Duplicate skipped: {job['url']}")

        return all_jobs


if __name__ == "__main__":
    scraper = OffreEmploiTnScraper()
    jobs = scraper.run()
    print(f"\nTotal new jobs saved: {len(jobs)}")
