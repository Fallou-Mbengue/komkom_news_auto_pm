import scrapy

class OpportunityItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    opportunity_type = scrapy.Field()
    eligibility_criteria = scrapy.Field()
    application_deadline = scrapy.Field()
    publication_date = scrapy.Field()
    # Ajoutez ici tout autre champ nécessaire selon votre usage.