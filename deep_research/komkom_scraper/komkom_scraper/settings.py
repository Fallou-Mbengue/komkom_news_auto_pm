BOT_NAME = "komkom_scraper"

SPIDER_MODULES = ["komkom_scraper.spiders"]
NEWSPIDER_MODULE = "komkom_scraper.spiders"

RETRY_ENABLED = True
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_ENABLED = True

ITEM_PIPELINES = {
    "komkom_scraper.pipelines.PostgresUpsertPipeline": 300,
}

DOWNLOADER_MIDDLEWARES = {
    "komkom_scraper.spiders.user_agent_rotation.UserAgentRotationMiddleware": 400,
}

ROBOTSTXT_OBEY = False
FEED_EXPORT_ENCODING = "utf-8"