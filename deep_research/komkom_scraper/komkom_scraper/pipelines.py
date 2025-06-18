import hashlib
import logging
import datetime
from sqlalchemy.orm import sessionmaker

# DB helpers are now located inside the Scrapy package
from komkom_scraper.db.db import (
    get_engine,
    create_tables,
    upsert_opportunity,
)

logger = logging.getLogger(__name__)


class PostgresUpsertPipeline:
    """Scrapy pipeline that performs an upsert of each scraped opportunity into Postgres."""

    def __init__(self):
        # Lazily build engine/session factory once per spider run
        self.engine = get_engine()
        create_tables(self.engine)
        self.Session = sessionmaker(bind=self.engine, future=True)

    @classmethod
    def from_crawler(cls, crawler):
        # Scrapy instantiation hook ➜ no settings needed for now
        return cls()

    def open_spider(self, spider):
        # Create a DB session at spider startup
        self.session = self.Session()

    def close_spider(self, spider):
        # Always cleanup the session
        self.session.close()

    def process_item(self, item, spider):
        # Generate a deterministic ID from the source_url so duplicates collapse
        item["id"] = hashlib.sha256(item["source_url"].encode()).hexdigest()
        now = datetime.datetime.utcnow()
        item["scraped_at"] = now
        item["updated_at"] = now

        try:
            upsert_opportunity(self.session, item)
        except Exception as exc:
            logger.error(
                "DB upsert failed for %s: %s", item.get("source_url", "<unknown>"), exc
            )
            # Re-raise so Scrapy knows something went wrong and can handle/retry as configured
            raise

        return item