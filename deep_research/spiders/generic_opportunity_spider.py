import scrapy
import yaml
import logging
from deep_research.items import OpportunityItem
from deep_research.utils.parsers import (
    clean_text, parse_date, parse_amount, derive_sector
)
import os
from urllib.parse import urljoin
from datetime import datetime

logger = logging.getLogger(__name__)


class GenericOpportunitySpider(scrapy.Spider):
    name = "generic_opportunity"
    custom_settings = {
        "RETRY_ENABLED": True,
        "DOWNLOAD_DELAY": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "ITEM_PIPELINES": {
            "deep_research.pipelines.PostgresUpsertPipeline": 300,
        },
        "DOWNLOADER_MIDDLEWARES": {
            "deep_research.spiders.user_agent_rotation.UserAgentRotationMiddleware": 400,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sources_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "sources.yaml"
        )
        with open(sources_path, "r", encoding="utf-8") as f:
            self.sources = yaml.safe_load(f)
        self.ban_counts = {}

    def start_requests(self):
        for source in self.sources:
            for url in source["start_urls"]:
                meta = {"source": source}
                yield scrapy.Request(
                    url=url,
                    meta=meta,
                    callback=self.parse_list,
                    errback=self.handle_error
                )

    def parse_list(self, response):
        source = response.meta["source"]
        list_selector = source["list_selector"]
        for elem in response.css(list_selector):
            item = OpportunityItem()
            item["source_id"] = source["id"]
            item["opportunity_type"] = source["type"]
            item["title"] = clean_text(
                "".join(elem.css(source["title_selector"]).getall())
            )
            item["description"] = clean_text(
                "".join(elem.css(source["description_selector"]).getall())
            )
            raw_link = elem.css(source["link_selector"]).get()
            item["source_url"] = urljoin(response.url, raw_link) if raw_link else response.url
            item["deadline"] = parse_date(
                "".join(elem.css(source["date_selector"]).getall())
            )
            item["sector"] = derive_sector(item["title"], item["description"])
            item["stage"] = None  # Derivation to be implemented later
            item["amount"] = parse_amount(item["description"])
            yield item

    def handle_error(self, failure):
        response = failure.value.response if hasattr(failure.value, "response") else None
        if response and response.status in (403, 429):
            domain = response.url.split("/")[2]
            self.ban_counts[domain] = self.ban_counts.get(domain, 0) + 1
            logger.warning(
                f"Ban detected ({response.status}) for {domain} "
                f"(count={self.ban_counts[domain]})"
            )