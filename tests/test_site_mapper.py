import boto3

import pytest
from tests.fixtures import *


def test_main(sqs):
    from lambdas.site_mapper import handler
    
    SQS_URL = os.environ['SQS_URL']
    _sqs = boto3.client('sqs')
    _sqs.create_queue(QueueName=SQS_URL)
    
    r = handler.main(Fixtures.site_mapper_sqs_message, None)
    assert r == 200


def test_send_message(sqs):
    from lambdas.site_mapper.handler import send_message
    
    SQS_URL = os.environ['SQS_URL']
    _sqs = boto3.client('sqs')
    _sqs.create_queue(QueueName=SQS_URL)
    
    r = send_message({"Id": "1", "MessageBody": "foo"})
    assert "Successful" in r.keys()


@pytest.mark.parametrize("url, expected", [
    ('https://www.foo.gov', ('foo', '', '')),
    ('https://www.bar.foo.gov', ('foo', 'bar', '')),
    ('https://www.fiz.bar.foo.gov', ('foo', 'fiz.bar', '')),
    ('https://www.foo.gov/baz', ('foo', '', 'baz')),
    ('https://www.foo.gov/baz/biz', ('foo', '', 'baz/biz')),
    ('https://www.bar.foo.gov/baz/biz', ('foo', 'bar', 'baz/biz')),
    ('https://www.fiz.foo.gov/bar', ('foo', 'fiz', 'bar')),
    ('https://foo.gov', ('foo', '', '')),
    ('https://bar.foo.gov', ('foo', 'bar', ''))
])
def test_format_url(url, expected):
    from lambdas.site_mapper.handler import MySpider
    result = MySpider.format_url(url)
    assert result == expected
