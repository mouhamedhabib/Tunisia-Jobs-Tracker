from scrapers.base_scraper import BaseScraper
from database.db import insert_job
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://www.farojob.net"
JOBS_URL = f"{BASE_URL}/jobs/page/"


class FarojobScraper(BaseScraper):
    """Scraper for farojob.net"""

    def __init__(self):
        super().__init__(
            source_name="farojob",
            base_url=BASE_URL
        )

    def parse_job(self, article) -> dict | None:
        """Extract job data from one article.loadmore-item element."""
        try:
            # Title and URL - inside h3.loop-item-title
            title_tag = article.select_one("h3.loop-item-title a")
            if not title_tag:
                return None
            title = title_tag.get_text(strip=True)
            url = title_tag.get("href", "")

            # Company - span.job-company > a > span
            company_tag = article.select_one("span.job-company a span")
            company = company_tag.get_text(strip=True) if company_tag else None

            # Contract type - span.job-type > a > span
            contract_tag = article.select_one("span.job-type a span")
            contract = contract_tag.get_text(strip=True) if contract_tag else None

            # Location - span.job-location > a > em
            location_tag = article.select_one("span.job-location a em")
            location = location_tag.get_text(strip=True) if location_tag else None

            # Split location into city and region
            city, region = None, None
            if location:
                parts = [p.strip() for p in location.split(",")]
                city = parts[0] if len(parts) > 0 else None
                region = parts[1] if len(parts) > 1 else None

            # Posted date - span.job-date__posted
            date_tag = article.select_one("span.job-date__posted")
            posted_at = date_tag.get_text(strip=True) if date_tag else None

            return {
                "title": title,
                "company": company,
                "city": city,
                "region": region,
                "contract": contract,
                "skills": None,
                "salary": None,
                "source": "farojob",
                "url": url,
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

            # All jobs are article.loadmore-item.noo_job
            articles = soup.select("article.loadmore-item.noo_job")

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
                        logger.info(f"Saved: {job['title']} @ {job['company']}")
                    else:
                        logger.info(f"Duplicate skipped: {job['url']}")

        return all_jobs


if __name__ == "__main__":
    scraper = FarojobScraper()
    jobs = scraper.run()
    print(f"\nTotal new jobs saved: {len(jobs)}")
