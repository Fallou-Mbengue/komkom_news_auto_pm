import scrapy


class OpportunityItem(scrapy.Item):
    id = scrapy.Field()
    source_id = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    deadline = scrapy.Field()
    opportunity_type = scrapy.Field()
    sector = scrapy.Field()
    stage = scrapy.Field()
    amount = scrapy.Field()
    source_url = scrapy.Field()
    scraped_at = scrapy.Field()
    updated_at = scrapy.Field()
    # New fields for eligibility and publication date
    eligibility_criteria = scrapy.Field()
    publication_date = scrapy.Field()