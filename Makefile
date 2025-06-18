.PHONY: crawl migrate test

crawl:
	scrapy crawl generic_opportunity

migrate:
	python -m deep_research.db

test:
	pytest tests