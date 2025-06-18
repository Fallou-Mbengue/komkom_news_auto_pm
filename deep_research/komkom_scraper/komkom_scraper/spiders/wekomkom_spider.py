"""
WekomkomSpider for Komkom Scraper - limited to 3 items, using refined selectors.

"""

import scrapy
from komkom_scraper.items import OpportunityItem
from komkom_scraper.utils.parsers import clean_text, parse_date
from urllib.parse import urlparse, parse_qs

class WekomkomSpider(scrapy.Spider):
    name = "wekomkom"
    allowed_domains = ["wekomkom.com"]
    start_urls = [
        "https://wekomkom.com/accompagnement?tag=accompagnement",
        "https://wekomkom.com/accompagnement?tag=opportunite",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_count = 0
        self.max_items = 3

    def parse(self, response):
        # Extract tag parameter from URL for opportunity_type
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)
        opportunity_type = query_params.get('tag', ['accompagnement'])[0]

        # Use the refined grid container selector
        container = response.css('div.grid.grid-cols-1.sm\\:grid-cols-2.md\\:grid-cols-2.xl\\:grid-cols-3.gap-4')
        for card in container.css('div'):
            if self.item_count >= self.max_items:
                return
            link = card.css('a.opportunity-link::attr(href)').get()
            if link:
                # Only pass opportunity_type
                yield response.follow(
                    link,
                    callback=self.parse_opportunity,
                    cb_kwargs={'opportunity_type': opportunity_type}
                )
                self.item_count += 1
                if self.item_count >= self.max_items:
                    return

        # Pagination logic (if we still need more)
        if self.item_count < self.max_items:
            next_url = response.css("a.next::attr(href)").get()
            if next_url:
                yield response.follow(response.urljoin(next_url), callback=self.parse)

    def parse_opportunity(self, response, opportunity_type):
        item = OpportunityItem()
        item['url'] = response.url
        item['source'] = 'Wekomkom'
        item['opportunity_type'] = opportunity_type
        item['title'] = clean_text(response.css('h1.opportunity-title::text').get())
        # description = concat of all child text nodes inside div.opportunity-description
        item['description'] = clean_text(' '.join(response.css('div.opportunity-description *::text').getall()))
        raw_pub = response.css('span.publication-date::text').get()
        item['publication_date'] = parse_date(raw_pub) if raw_pub else None
        raw_deadline = response.css('span.application-deadline::text').get()
        item['application_deadline'] = parse_date(raw_deadline) if raw_deadline else None
        item['eligibility_criteria'] = clean_text(response.css('div.eligibility-criteria::text').get())
        yield item