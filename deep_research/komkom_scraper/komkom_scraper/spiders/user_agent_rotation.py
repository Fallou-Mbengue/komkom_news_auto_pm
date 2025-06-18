"""
Downloader middleware for rotating User-Agent headers in Scrapy spiders.

This module provides the UserAgentRotationMiddleware, which sets a random User-Agent
string from a predefined list for each outgoing HTTP request. This helps to reduce
the likelihood of detection and blocking by target websites due to repetitive user agents.
"""

from scrapy import signals
import random

class UserAgentRotationMiddleware:
    """Downloader middleware that rotates the User-Agent header for each request."""

    # List of common User-Agent strings. Extend/modify as needed.
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.76",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 OPR/94.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    ]

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def process_request(self, request, spider):
        """Select a random User-Agent string and set it for the outgoing request."""
        user_agent = random.choice(self.USER_AGENTS)
        request.headers["User-Agent"] = user_agent
        spider.logger.debug(f"Using User-Agent: {user_agent}")
        # Continue processing the request in the downloader chain
        return None

    def spider_opened(self, spider):
        spider.logger.info(f"UserAgentRotationMiddleware enabled for spider {spider.name}")