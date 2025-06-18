BOT_NAME = "deep_research"

SPIDER_MODULES = ["deep_research.spiders"]
NEWSPIDER_MODULE = "deep_research.spiders"

# Core defaults so we don't have to duplicate them inside each spider:
RETRY_ENABLED = True
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_ENABLED = True

ITEM_PIPELINES = {
    "deep_research.pipelines.PostgresUpsertPipeline": 300,
}

DOWNLOADER_MIDDLEWARES = {
    "deep_research.spiders.user_agent_rotation.UserAgentRotationMiddleware": 400,
}

ROBOTSTXT_OBEY = False
FEED_EXPORT_ENCODING = "utf-8"

# (Leave database credentials, etc. to environment variables, as handled by deep_research.db.)