"""
Wekomkom Spider for Komkom News Deep Research

Assumptions:
- HTML structure is hypothetical, selectors below may need adjustment after real markup inspection.
- Each opportunity card: &lt;article class="opportunity-card"&gt;.
- Link to details: h2 a::attr(href)
- Title: h2 a::text
- Short description: p.summary::text
- Deadline: span.deadline::text
- Publication date: span.pub-date::text (may be missing)
- Pagination: a.next::attr(href)
- On detail page, eligibility: div.eligibility or h3:-sibling lists, fallback to list
"""

import scrapy
from deep_research.items import OpportunityItem
from deep_research.utils.parsers import clean_text, parse_date, parse_amount

class WekomkomSpider(scrapy.Spider):
    name = "wekomkom"
    allowed_domains = ["wekomkom.com"]
    start_urls = ["https://wekomkom.com/accompagnement"]

    custom_settings = {
        # Use the same pipeline, UA rotation, delays as generic spider (assume settings are global/default)
    }

    def parse(self, response):
        for card in response.css("article.opportunity-card"):
            link = card.css("h2 a::attr(href)").get()
            title = card.css("h2 a::text").get()
            short_desc = card.css("p.summary::text").get()
            deadline_raw = card.css("span.deadline::text").get()
            pub_date_raw = card.css("span.pub-date::text").get()
            # Compose absolute link if needed
            url = response.urljoin(link) if link else None

            # Prepare meta for detail page
            meta = {
                "source_id": url,  # fallback, as real ID unknown
                "title": clean_text(title),
                "short_desc": clean_text(short_desc),
                "deadline": parse_date(deadline_raw),
                "source_url": url,
                "publication_date": parse_date(pub_date_raw) if pub_date_raw else None,
            }

            if link:
                yield response.follow(
                    url,
                    callback=self.parse_opportunity,
                    meta=meta
                )
            else:
                # fallback: yield item from list page if no detail
                item = OpportunityItem(
                    id=None,
                    source_id=meta["source_id"],
                    title=meta["title"],
                    description=meta["short_desc"],
                    deadline=meta["deadline"],
                    opportunity_type="accompagnement",
                    sector=None,
                    stage=None,
                    amount=None,
                    source_url=meta["source_url"],
                    scraped_at=None,
                    updated_at=None,
                    eligibility_criteria=None,
                    publication_date=meta["publication_date"],
                )
                yield item

        # pagination
        next_url = response.css("a.next::attr(href)").get()
        if next_url:
            yield response.follow(response.urljoin(next_url), callback=self.parse)

    def parse_opportunity(self, response):
        # Use meta from list page
        meta = response.meta
        # Extract long description
        desc_parts = response.css("div.description *::text").getall()
        if not desc_parts:
            desc_parts = response.css("section.long-desc *::text").getall()
        desc = clean_text(" ".join(desc_parts)) if desc_parts else meta.get("short_desc")

        # Eligibility: div.eligibility, or any h3 containing 'Eligibil' and its next sibling list
        eligibility = None
        elig_div = response.css("div.eligibility *::text").getall()
        if elig_div:
            eligibility = clean_text(" ".join(elig_div))
        else:
            for h3 in response.css("h3"):
                h3_text = h3.css("::text").get()
                if h3_text and "eligibil" in h3_text.lower():
                    sibling = h3.xpath("following-sibling::*[1]")
                    sibling_text = sibling.css("*::text").getall()
                    eligibility = clean_text(" ".join(sibling_text)) if sibling_text else None
                    break
        if not eligibility:
            eligibility = meta.get("short_desc")

        # Amount: try to extract from detail page if available
        amount_raw = response.css("span.amount::text, .grant-amount::text").get()
        amount = parse_amount(amount_raw) if amount_raw else None

        item = OpportunityItem(
            id=None,
            source_id=meta["source_id"],
            title=meta["title"],
            description=desc,
            deadline=meta["deadline"],
            opportunity_type="accompagnement",
            sector=None,
            stage=None,
            amount=amount,
            source_url=meta["source_url"],
            scraped_at=None,
            updated_at=None,
            eligibility_criteria=eligibility,
            publication_date=meta.get("publication_date"),
        )
        yield item