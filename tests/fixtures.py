import json
import os

import boto3
from moto import mock_s3, mock_sqs
import pytest


class Fixtures(object):
    site_mapper_sqs_message_path = os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))),
        'tests/assets/sqsMessage.json'
    )
    with open(site_mapper_sqs_message_path) as f:
        site_mapper_sqs_message = json.load(f)


@pytest.fixture()
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['TEST_ENV'] = '1'
    os.environ['SQS_URL'] = 'test'
    os.environ['BUCKET_NAME'] = 'test'
    os.environ['OBJECT_KEY'] = 'test.csv'


@pytest.fixture(scope='function')
def s3(aws_credentials):
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')


@pytest.fixture(scope='function')
def sqs(aws_credentials):
    with mock_sqs():
        yield boto3.client('sqs', region_name='us-east-1')
