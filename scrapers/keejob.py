from scrapers.base_scraper import BaseScraper
from database.db import insert_job
import logging
import re

logger = logging.getLogger(__name__)

BASE_URL = "https://www.keejob.com"
JOBS_URL = f"{BASE_URL}/offres-emploi/?page="


class KeejobScraper(BaseScraper):
    """Scraper for keejob.com"""

    def __init__(self):
        super().__init__(
            source_name="keejob",
            base_url=BASE_URL
        )

    def parse_job(self, article) -> dict | None:
        """Extract job data from one article element."""
        try:
            # Title and URL - h2 > a
            title_tag = article.select_one("h2 a")
            if not title_tag:
                return None
            title = title_tag.get_text(strip=True)
            url = BASE_URL + title_tag.get("href", "")

            # Company - p > a with text-blue class
            company_tag = article.select_one("p a[class*='text-blue']")
            if not company_tag:
                # Anonymous company
                anon = article.select_one("p span")
                company = anon.get_text(strip=True) if anon else None
            else:
                company = company_tag.get_text(strip=True)

            # All spans with icons - extract by icon type
            contract, salary, sector = None, None, None

            for span in article.select("span[class*='inline-flex']"):
                icon = span.select_one("i")
                if not icon:
                    continue
                icon_class = icon.get("class", [])
                text = span.get_text(strip=True)
                # Remove icon text artifacts
                text = re.sub(r'\s+', ' ', text).strip()

                if "fa-briefcase" in " ".join(icon_class):
                    if contract:
                        contract = contract + " / " + text
                    else:
                        contract = text
                elif "fa-money-bill-wave" in " ".join(icon_class):
                    salary = text
                elif "fa-industry" in " ".join(icon_class):
                    sector = text

            # Location - div with fa-map-marker-alt > span
            location, city, region = None, None, None
            loc_tag = article.find("i", class_="fa-map-marker-alt")
            if loc_tag:
                city_span = loc_tag.find_next_sibling("span")
                location = city_span.get_text(strip=True) if city_span else None
                parts = [p.strip() for p in location.split(",")] if location else []
                city = parts[0] if len(parts) > 0 else None
                region = parts[1] if len(parts) > 1 else None
            else:
                location, city, region = None, None, None

            # Date - span with fa-clock
            date_tag = article.select_one("div:has(i.fa-clock) span")
            posted_at = date_tag.get_text(strip=True) if date_tag else None

            return {
                "title": title,
                "company": company,
                "city": city,
                "region": region,
                "contract": contract,
                "skills": sector,     # Using skills field for sector
                "salary": salary,
                "source": "keejob",
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
            url = f"{JOBS_URL}{page_num}"
            soup = self.get_page(url)

            if not soup:
                logger.warning(f"Failed to fetch page {page_num} - stopping")
                break

            articles = soup.select("article")

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
    scraper = KeejobScraper()
    jobs = scraper.run()
    print(f"\nTotal new jobs saved: {len(jobs)}")
