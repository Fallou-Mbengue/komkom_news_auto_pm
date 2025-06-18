.PHONY: crawl migrate test

crawl:
	scrapy crawl generic_opportunity

migrate:
	python -m deep_research.komkom_scraper.komkom_scraper.db.db

test:
	pytest tests