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
        self.scraped_count = 0

    def parse(self, response):
        # Extract tag parameter from URL for opportunity_type
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)
        opportunity_type = query_params.get('tag', ['accompagnement'])[0]

        # Refined grid and card selectors
        grid_selector = 'div.grid.grid-cols-1.sm\\:grid-cols-2.md\\:grid-cols-2.xl\\:grid-cols-3.gap-4'
        card_selector = 'div.flex.flex-col.border.border-th-gray-dfe.bg-white.rounded-\\[20px\\]'

        grid = response.css(grid_selector)
        cards = grid.css(card_selector) if grid else []

        for card in cards:
            if self.scraped_count >= 3:
                self.crawler.engine.close_spider(self, "Scraped limit reached")
                return

            # Try to find detail URL from data-url or data-href
            detail_url = card.attrib.get('data-url') or card.attrib.get('data-href')

            if detail_url:
                self.scraped_count += 1
                yield response.follow(
                    detail_url,
                    callback=self.parse_opportunity,
                    cb_kwargs={'opportunity_type': opportunity_type}
                )
            else:
                # Fallback: yield minimal OpportunityItem from card itself
                item = OpportunityItem()
                item['title'] = clean_text(
                    card.css('h3.text-th-gray-22.font-bold.text-base.mb-4.md\\:my-1.line-clamp-3::text').get()
                )
                item['url'] = response.url
                item['source'] = 'Wekomkom'
                item['opportunity_type'] = opportunity_type
                item['description'] = None
                item['publication_date'] = None
                item['application_deadline'] = None
                item['eligibility_criteria'] = None
                self.scraped_count += 1
                yield item

            if self.scraped_count >= 3:
                self.crawler.engine.close_spider(self, "Scraped limit reached")
                return

        # Pagination logic (if we still need more)
        if self.scraped_count < 3:
            next_url = response.css("a.next-page::attr(href)").get()
            if next_url:
                yield response.follow(response.urljoin(next_url), callback=self.parse)

    def parse_opportunity(self, response, opportunity_type):
        item = OpportunityItem()
        item['url'] = response.url
        item['source'] = 'Wekomkom'
        item['opportunity_type'] = opportunity_type

        title = clean_text(response.css('h1.opportunity-title::text').get())
        self.logger.debug(f"Title: {title}")
        item['title'] = title

        # description = concat of all child text nodes inside div.opportunity-description
        description = clean_text(' '.join(response.css('div.opportunity-description *::text').getall()))
        self.logger.debug(f"Description: {description}")
        item['description'] = description

        raw_pub = response.css('span.publication-date::text').get()
        publication_date = parse_date(raw_pub) if raw_pub else None
        self.logger.debug(f"Publication Date: {publication_date}")
        item['publication_date'] = publication_date

        raw_deadline = response.css('span.application-deadline::text').get()
        application_deadline = parse_date(raw_deadline) if raw_deadline else None
        self.logger.debug(f"Application Deadline: {application_deadline}")
        item['application_deadline'] = application_deadline

        eligibility = clean_text(response.css('div.eligibility-criteria::text').get())
        self.logger.debug(f"Eligibility: {eligibility}")
        item['eligibility_criteria'] = eligibility

        yield item