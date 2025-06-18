"""
WekomkomSpider for Komkom Scraper - limited to 3 items

Based on: deep_research/spiders/wekomkom_spider.py
"""

import scrapy
from komkom_scraper.items import OpportunityItem
from deep_research.utils.parsers import clean_text, parse_date, parse_amount

class WekomkomSpider(scrapy.Spider):
    name = "wekomkom"
    allowed_domains = ["wekomkom.com"]
    start_urls = ["https://wekomkom.com/accompagnement"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_count = 0
        self.max_items = 3

    def parse(self, response):
        for card in response.css("article.opportunity-card"):
            if self.item_count >= self.max_items:
                return
            link = card.css("h2 a::attr(href)").get()
            title = card.css("h2 a::text").get()
            short_desc = card.css("p.summary::text").get()
            deadline_raw = card.css("span.deadline::text").get()
            pub_date_raw = card.css("span.pub-date::text").get()
            url = response.urljoin(link) if link else None

            meta = {
                "source_id": url,
                "title": clean_text(title),
                "short_desc": clean_text(short_desc),
                "deadline": parse_date(deadline_raw),
                "source_url": url,
                "publication_date": parse_date(pub_date_raw) if pub_date_raw else None,
            }

            if link:
                if self.item_count >= self.max_items:
                    return
                yield response.follow(
                    url,
                    callback=self.parse_opportunity,
                    meta=meta
                )
                self.item_count += 1
            else:
                if self.item_count >= self.max_items:
                    return
                item = OpportunityItem(
                    id=None,
                    source_id=meta["source_id"],
                    title=meta["title"],
                    description=meta["short_desc"],
                    deadline=meta["deadline"],
                    opportunity_type="accompagnement",
                    sector=None,
                    stage=None,
                    amount=None,
                    source_url=meta["source_url"],
                    scraped_at=None,
                    updated_at=None,
                    eligibility_criteria=None,
                    publication_date=meta["publication_date"],
                )
                yield item
                self.item_count += 1

        if self.item_count < self.max_items:
            next_url = response.css("a.next::attr(href)").get()
            if next_url:
                yield response.follow(response.urljoin(next_url), callback=self.parse)

    def parse_opportunity(self, response):
        if self.item_count > self.max_items:
            return
        meta = response.meta
        desc_parts = response.css("div.description *::text").getall()
        if not desc_parts:
            desc_parts = response.css("section.long-desc *::text").getall()
        desc = clean_text(" ".join(desc_parts)) if desc_parts else meta.get("short_desc")

        eligibility = None
        elig_div = response.css("div.eligibility *::text").getall()
        if elig_div:
            eligibility = clean_text(" ".join(elig_div))
        else:
            for h3 in response.css("h3"):
                h3_text = h3.css("::text").get()
                if h3_text and "eligibil" in h3_text.lower():
                    sibling = h3.xpath("following-sibling::*[1]")
                    sibling_text = sibling.css("*::text").getall()
                    eligibility = clean_text(" ".join(sibling_text)) if sibling_text else None
                    break
        if not eligibility:
            eligibility = meta.get("short_desc")

        amount_raw = response.css("span.amount::text, .grant-amount::text").get()
        amount = parse_amount(amount_raw) if amount_raw else None

        item = OpportunityItem(
            id=None,
            source_id=meta["source_id"],
            title=meta["title"],
            description=desc,
            deadline=meta["deadline"],
            opportunity_type="accompagnement",
            sector=None,
            stage=None,
            amount=amount,
            source_url=meta["source_url"],
            scraped_at=None,
            updated_at=None,
            eligibility_criteria=eligibility,
            publication_date=meta.get("publication_date"),
        )
        yield item