import json
import random
from urllib.parse import urljoin, urlparse

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import IGNORED_EXTENSIONS, LinkExtractor
from scrapy.crawler import CrawlerProcess
import scrapy
from twisted.internet import reactor

from send_message import send_message


USER_AGENTS = [
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/57.0.2987.110 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/61.0.3163.79 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) '
     'Gecko/20100101 '
     'Firefox/55.0'),  # firefox
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/61.0.3163.91 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/62.0.3202.89 '
     'Safari/537.36'),  # chrome
    ('Mozilla/5.0 (X11; Linux x86_64) '
     'AppleWebKit/537.36 (KHTML, like Gecko) '
     'Chrome/63.0.3239.108 '
     'Safari/537.36'),  # chrome
]


class MySpider(CrawlSpider):

    LINKS = set()
    UNWANTED = {'mailto', 'tel:', 'javascript', 'youtube.com', 'twitter.com'}
    
    custom_settings = {
        'LOG_ENABLED': False,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 400, 408, 429],
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_PORT': None,
        'TELNETCONSOLE_ENABLED': False
    }
    

    def _process_request(self, req):
        url = req.url
        if url.lower().endswith(tuple(IGNORED_EXTENSIONS)):
            raise scrapy.exceptions.IgnoreRequest
        new_url = url.split("?")[0]
        new_url = new_url.split("#")[0]
        if any(x in new_url for x in self.UNWANTED):
            raise scrapy.exceptions.IgnoreRequest
        elif new_url not in self.LINKS and self.parsed_url.netloc in new_url:
            req = req.replace(url=new_url)
            return req
        else:
            raise scrapy.exceptions.IgnoreRequest

    
    def parse_item(self, response):
        item = scrapy.Item()
        yield item

        for url in response.xpath('//a/@href').extract():
            if url and not url.startswith('#'):
                url = urljoin(response.url, url)
                
                if url.lower().endswith(tuple(IGNORED_EXTENSIONS)):
                    continue
                
                url = url.split("?")[0]
                url = url.split("#")[0]
                
                if any(x in url for x in self.UNWANTED):
                    continue
                
                elif self.parsed_url.netloc in url and url not in self.LINKS:
                    try:
                        scrapy.http.Request(
                            url,
                            meta={
                                'dont_redirect': True,
                                'download_timeout': 20
                            }
                        )
                    except Exception:
                        continue
                    
                    path = urlparse(url).path
                    path = path if path != '/' else ''
                    path = path[1:] if path.startswith('/') else path
                    path = path.replace("/", "+")
                    # partitionKey is agency+org+domain+subdomain+path
                    db_id = (
                        f'{self.agency}+{self.organization}+'
                        f'{self.domain}+{self.subdomain}+{path}'
                    )
                    
                    msg_body = json.dumps(dict(
                        Agency=self.agency,
                        Organization=self.organization,
                        domain=self.domain,
                        subdomain=self.subdomain,
                        tld=self.tld,
                        routeable_url=self.start_urls[0],
                        db_id=db_id
                    ))

                    entry = {'Id': '1', 'MessageBody': msg_body}
                    send_message(entry)

                    self.LINKS.add(url)

                else:
                    pass


def scrape(routeable_url=None, domain=None, tld='gov', subdomain='', **kwargs):
    full_dom = f'{subdomain}.{domain}.{tld}'if subdomain else f'{domain}.{tld}'
    MySpider.parsed_url = urlparse(routeable_url)
    MySpider.subdomain = subdomain
    MySpider.domain = domain
    MySpider.tld = tld
    MySpider.name = full_dom
    MySpider.allow_domains = [full_dom]
    MySpider.start_urls = [routeable_url]
    MySpider.agency = kwargs.get('Agency', '')
    MySpider.organization = kwargs.get('Organization', '')
    
    MySpider.allow = (
        rf'^.*{MySpider.parsed_url.netloc}.*$'
    )
    
    MySpider.deny = (
        r'^[^\/]*(?:\/[^\/]*){6,}$',  # 6 or more slashes
        r'mailto',
        r'tel:',
        r'javascript',
        r'youtube.com',
        r'twitter.com'
    )

    MySpider.rules = (
        Rule(
            LinkExtractor(
                allow_domains=MySpider.allow_domains,
                allow=MySpider.allow,
                deny=MySpider.deny
            ),
            callback='parse_item',
            follow=True,
            process_request='_process_request'
        ),
    )

    process = CrawlerProcess({
        'USER_AGENT': random.choice(USER_AGENTS)
    })
    d = process.crawl(MySpider)
    d.addCallback(lambda _: reactor.stop())
    reactor.run()
