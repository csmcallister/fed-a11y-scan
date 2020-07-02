import json

from tests.fixtures import *


def test_main(sqs, s3):
    from lambdas.domain_gatherer import handler
    
    BUCKET = os.environ['BUCKET_NAME']
    OBJ_KEY = os.environ['OBJECT_KEY']
    SQS_URL = os.environ['SQS_URL']
    s3.create_bucket(Bucket=BUCKET)
    with open('domains/domains.csv', 'rb') as f:
        s3.upload_fileobj(f, BUCKET, OBJ_KEY)
    
    sqs.create_queue(QueueName=SQS_URL)

    r = handler.main({}, None)
    assert r == 200


def test_grouper():
    from lambdas.domain_gatherer.handler import grouper
    result = list(grouper(2, range(10)))
    expected = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
    assert result == expected


def test_send_sqs_messages(sqs):
    from lambdas.domain_gatherer.handler import send_sqs_messages

    SQS_URL = os.environ['SQS_URL']
    sqs.create_queue(QueueName=SQS_URL)
    r = send_sqs_messages(
        [json.dumps({'foo': 'bar'}), json.dumps({'biz': 'baz'})], 
        sqs_queue_url=SQS_URL
    )
    assert "Successful" in r.keys()