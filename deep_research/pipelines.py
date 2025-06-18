import hashlib
import logging
import datetime
from sqlalchemy.orm import sessionmaker
from deep_research.db import get_engine, create_tables, upsert_opportunity

logger = logging.getLogger(__name__)


class PostgresUpsertPipeline:
    def __init__(self):
        self.engine = get_engine()
        create_tables(self.engine)
        self.Session = sessionmaker(bind=self.engine, future=True)

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        self.session = self.Session()

    def close_spider(self, spider):
        self.session.close()

    def process_item(self, item, spider):
        # Compute SHA256 of source_url
        item['id'] = hashlib.sha256(item['source_url'].encode()).hexdigest()
        item['scraped_at'] = datetime.datetime.utcnow()
        item['updated_at'] = datetime.datetime.utcnow()
        try:
            upsert_opportunity(self.session, item)
        except Exception as e:
            logger.error(f"DB upsert failed for {item['source_url']}: {e}")
            raise
        return item