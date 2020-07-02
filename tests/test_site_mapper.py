import boto3

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
