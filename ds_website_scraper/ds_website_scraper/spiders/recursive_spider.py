import scrapy
from urllib.parse import urlparse
import json
import re
from bs4 import BeautifulSoup, NavigableString, Tag
from crawl4ai import AsyncWebCrawler
 
def is_domain_allowed(url, allowed_domains):
 
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
 
    if domain.startswith("www."):
        domain = domain[4:]
 
    return any(
        domain == allowed.lower() or domain.endswith(f".{allowed.lower()}")
        for allowed in allowed_domains
    )
 
class RecursiveSpider(scrapy.Spider):
    name = "recursive_spider"
 
    # DON'T Change theese settings! We can't overload the website!
    custom_settings = {
        "DEPTH_LIMIT": 2,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "DOWNLOAD_DELAY": 1,
        "RETRY_TIMES": 5,
        "TELNETCONSOLE_ENABLED": False,
        "FEED_EXPORT_ENCODING": "utf-8",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en",
        },
    }
 
    start_urls = ["https://www.datasport.com/en/"]
    allowed_domains = ["datasport.com"]
 
    site_structure = {"site": start_urls[0], "pages": []}
    visited = set()
 
    def parse(self, response):
        """Parse a single page, extract content, and process with Crawl4AI."""
 
        current_url = response.url
        self.visited.add(current_url)
 
        page_title = response.css("title::text").get(default="No Title").strip()
        page_content = response.body.decode("utf-8")  # Get raw HTML content
 
        # Call Crawl4AI for structured extraction asynchronously
        structured_markdown = asyncio.run(self.extract_structured_data(page_content))
 
        internal_links = set()
        external_links = set()
 
        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
 
            if is_domain_allowed(full_url, self.allowed_domains):
                internal_links.add(full_url)
            else:
                external_links.add(full_url)
 
        page_info = {
            "url": current_url,
            "title": page_title,
            "content": structured_markdown,  # Use extracted Markdown from Crawl4AI
            "links": {
                "internal": list(internal_links),
                "external": list(external_links),
            },
        }
 
        subpage_futures = []
        for link in internal_links:
            if link not in self.visited:
                subpage_futures.append(scrapy.Request(url=link, callback=self.parse))
 
        self.site_structure["pages"].append(page_info)
 
        yield from subpage_futures
 
    async def extract_structured_data(self, raw_html):
        """Extract structured Markdown using Crawl4AI."""
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(content=raw_html)
            return result.markdown
 
    def closed(self, reason):
        """Save site structure when crawling is finished."""
        with open("data/site_structure.json", "w") as f:
            json.dump(self.site_structure, f, indent=4)
