import json
import logging
import os
import random
import sys
from urllib.parse import urljoin, urlparse

import boto3
from botocore.exceptions import ClientError
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import IGNORED_EXTENSIONS, LinkExtractor
from scrapy.crawler import CrawlerProcess
import scrapy
from twisted.internet import reactor


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(asctime)s: %(message)s'
)
sqs_client = boto3.client('sqs', 'us-east-1')
SQS_URL = os.getenv('SQS_URL')
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


def log_helper(logger, e, event):
    logger.critical('## EXCEPTION')
    logger.critical(e, exc_info=True)
    logger.critical('## EVENT')
    logger.critical(event)


def send_message(entry):
    try:
        return sqs_client.send_message_batch(
            QueueUrl=SQS_URL,
            Entries=[entry]
        )

    except ClientError as e:  # pragma: no cover
        err_msg = f'{e} with {e.response}'
        logger.error(err_msg, exc_info=True)


class MySpider(CrawlSpider):  # pragma: no cover

    LINKS = set()
    UNWANTED = {'mailto', 'tel:', 'javascript', 'youtube.com', 'twitter.com'}
    
    custom_settings = {
        'LOG_ENABLED': False,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 400, 408, 429],
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_PORT': None,
        'TELNETCONSOLE_ENABLED': False
    }
    
    
    @staticmethod
    def format_url(url):
        parsed_url = urlparse(url)
        path = parsed_url.path
        path = path if path != '/' else ''
        path = path[1:] if path.startswith('/') else path
        domains = parsed_url.netloc.split('.gov')[0].split(".")
        domain = domains.pop(-1)
        try:
            domains.remove('www')
        except ValueError:
            pass
        subdomain = ".".join(domains)

        return domain, subdomain, path
    
    
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
                    except Exception:  # pragma: no cover
                        continue

                    domain, subdomain, path = MySpider.format_url(url)

                    # partitionKey is agency+org+domain+subdomain+path
                    db_id = (
                        f'{self.agency}+{self.organization}+'
                        f'{domain}+{subdomain}+{path}'
                    )
                    
                    msg_body = json.dumps(dict(
                        Agency=self.agency,
                        Organization=self.organization,
                        domain=domain,
                        subdomain=subdomain,
                        tld='gov',
                        routeable_url=url,
                        db_id=db_id
                    ))

                    entry = {'Id': '1', 'MessageBody': msg_body}
                    send_message(entry)

                    self.LINKS.add(url)


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


def main(event, context):
    
    body = json.loads(event['Records'][0]['body'])
    
    try:
        scrape(**body)
    except Exception as e:  # pragma: no cover
        log_helper(logger, e, event)
        sys.exit(1)
    # Without the sys.exit, subsequent executions raise ReactorNotRestartable
    # TODO: figure out how to reuse reactor across executions
    if os.environ.get('TEST_ENV'):
        return 200
    sys.exit(0)  # pragma: no cover