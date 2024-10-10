import scrapy
from urllib.parse import urlparse
import json
import re
from bs4 import BeautifulSoup, NavigableString, Tag


def is_domain_allowed(url, allowed_domains):

    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return any(
        domain == allowed.lower() or domain.endswith(f".{allowed.lower()}")
        for allowed in allowed_domains
    )


def remove_empty_and_simplify(node):
    if not node.get_text(strip=True) and not isinstance(node, NavigableString):
        node.decompose()
        return None

    if len(node.contents) == 1 and isinstance(node.contents[0], (BeautifulSoup, str)):
        simplified_content = remove_empty_and_simplify(node.contents[0])
        if simplified_content:
            node.replace_with(simplified_content)
        return simplified_content

    for child in list(node.contents):
        remove_empty_and_simplify(child)

    return node


def remove_empty_and_simplify(node):
    if isinstance(node, NavigableString):
        return node if node.strip() else None

    if not isinstance(node, Tag):
        return None

    if not node.get_text(strip=True):
        node.decompose()
        return None

    if len(node.contents) == 1 and isinstance(node.contents[0], (NavigableString, Tag)):
        simplified_content = remove_empty_and_simplify(node.contents[0])
        if simplified_content:
            node.replace_with(simplified_content)
        return simplified_content

    for child in list(node.contents):
        remove_empty_and_simplify(child)

    return node


class RecursiveSpider(scrapy.Spider):

    name = "recursive_spider"

    custom_settings = {"DEPTH_LIMIT": 6}

    start_urls = ["https://www.datasport.com/en/", "https://www.datasport.com/en/erv/"]
    allowed_domains = ["datasport.com"]

    site_structure = {"site": start_urls[0], "pages": []}
    visited = set()

    def parse(self, response):
        """Parse a single page and extract content and links."""

        current_url = response.url
        self.visited.add(current_url)

        page_title = response.css("title::text").get(default="No Title").strip()
        page_content = self.parse_content(response)

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
            "content": page_content,
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

    def closed(self, reason):
        with open("data/site_structure.json", "w") as f:
            json.dump(self.site_structure, f, indent=4)

    def parse_content(self, response):

        body_html = response.xpath("//body").get()

        soup = BeautifulSoup(body_html, "html.parser")

        for tag in soup(["script", "style", "noscript", "meta"]):
            tag.decompose()

        for tag in soup.find_all(True):
            tag.attrs = {}

        simplified_soup = remove_empty_and_simplify(soup.body)

        simplified_html = str(simplified_soup)

        cleaned_content = re.sub(r"[\r\n\t]+", "", simplified_html)
        cleaned_content = re.sub(r"\s{2,}", " ", cleaned_content)

        return cleaned_content
