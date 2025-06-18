import scrapy

class OpportunityItem(scrapy.Item):
    id = scrapy.Field()
    source_id = scrapy.Field()  # Correspond à la colonne source_id en DB
    title = scrapy.Field()
    description = scrapy.Field()
    source_url = scrapy.Field() # <-- Champ renommé pour correspondre à la DB
    source = scrapy.Field()     # Nom de la source (ex: "Google Search")
    opportunity_type = scrapy.Field()
    eligibility_criteria = scrapy.Field()
    # Note : 'deadline' en DB correspond à 'application_deadline' dans l'item Scrapy
    application_deadline = scrapy.Field()
    publication_date = scrapy.Field()
    sector = scrapy.Field()
    stage = scrapy.Field()
    amount = scrapy.Field()
    scraped_at = scrapy.Field() # Correspond à la colonne scraped_at en DB
    updated_at = scrapy.Field() # Correspond à la colonne updated_at en DB