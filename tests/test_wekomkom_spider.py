"""
Unit tests for WekomkomSpider

Assumptions:
- HTML selectors are hypothetical and may need adjustment once real markup is available.
"""

import pytest
from scrapy.http import HtmlResponse, Request
from deep_research.spiders.wekomkom_spider import WekomkomSpider

@pytest.fixture
def list_html():
    return """
    <html>
      <body>
        <article class="opportunity-card">
          <h2><a href="/accompagnement/opp-1">Accompagnement Alpha</a></h2>
          <p class="summary">Pour startups early-stage. Eligibilité: résider en France.</p>
          <span class="deadline">2024-07-31</span>
          <span class="pub-date">2024-06-10</span>
        </article>
        <a class="next" href="/accompagnement?page=2">Suivant</a>
      </body>
    </html>
    """

@pytest.fixture
def detail_html():
    return """
    <html>
      <body>
        <div class="description">
          <p>Programme intensif pour startups tech. Détails: mentorat, ateliers, réseautage.</p>
        </div>
        <div class="eligibility">
          <ul>
            <li>Société basée en France</li>
            <li>Moins de 5 ans</li>
          </ul>
        </div>
        <span class="amount">€10 000</span>
      </body>
    </html>
    """

def test_parse_list(monkeypatch, list_html):
    spider = WekomkomSpider()
    url = "https://wekomkom.com/accompagnement"
    response = HtmlResponse(url=url, body=list_html, encoding="utf-8")

    # Patch parse_opportunity so we can test meta passing without following
    results = []
    def fake_follow(url, callback, meta):
        results.append((url, meta))
    monkeypatch.setattr(response, "follow", fake_follow)

    list(spider.parse(response))
    assert results, "Should try to follow detail page link"
    href, meta = results[0]
    assert href.endswith("/accompagnement/opp-1")
    assert meta["title"] == "Accompagnement Alpha"
    assert meta["deadline"].isoformat() == "2024-07-31"
    assert meta["publication_date"].isoformat() == "2024-06-10"
    assert "Eligibilité" in meta["short_desc"]

def test_parse_opportunity(detail_html):
    from scrapy.http import Request
    spider = WekomkomSpider()
    meta = {
        "source_id": "https://wekomkom.com/accompagnement/opp-1",
        "title": "Accompagnement Alpha",
        "short_desc": "Pour startups early-stage. Eligibilité: résider en France.",
        "deadline": None,
        "source_url": "https://wekomkom.com/accompagnement/opp-1",
        "publication_date": None,
    }
    url = meta["source_url"]
    response = HtmlResponse(
        url=url,
        body=detail_html,
        encoding="utf-8",
        request=Request(url, meta=meta),
    )
    # Attach meta manually as in Scrapy
    response.meta = meta
    items = list(spider.parse_opportunity(response))
    assert len(items) == 1
    item = items[0]
    assert item["title"] == "Accompagnement Alpha"
    assert "intensif" in item["description"]
    assert item["eligibility_criteria"].startswith("Société basée")
    assert item["amount"] == 10000
    assert item["opportunity_type"] == "accompagnement"