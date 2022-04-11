import csv
from itertools import zip_longest
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(asctime)s: %(message)s'
)

BUCKET_NAME = os.getenv('BUCKET_NAME')
OBJECT_KEY = os.getenv('OBJECT_KEY')
SQS_URL = os.getenv('SQS_URL')
sqs_client = boto3.client('sqs')
s3 = boto3.resource(u's3')


def log_helper(logger, e, event):  # pragma: no cover
    logger.error('## EXCEPTION')
    logger.error(e, exc_info=True)
    logger.error('## ENV VARS')
    logger.error(os.environ)
    logger.error('## EVENT')
    logger.error(event)


def grouper(n, iterable, fillvalue=None):
    '''Group iterable into batches of n items, e.g. to send 10 items to SQS.'''
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def send_sqs_messages(msg_bodies, sqs_queue_url=SQS_URL):
    entries = []
    for i, msg_body in enumerate(msg_bodies):
        if msg_body:
            entries.append({'Id': str(i), 'MessageBody': msg_body})
    
    try:
        return sqs_client.send_message_batch(
            QueueUrl=sqs_queue_url,
            Entries=entries
        )
    except ClientError as e:  # pragma: no cover
        err_msg = f'{e} with {e.response}'
        logger.error(err_msg, exc_info=True)
    except Exception as e:  # pragma: no cover
        logger.error(f'{e}', exc_info=True)


def get_domains():
    bucket = s3.Bucket(BUCKET_NAME)
    obj = bucket.Object(key=OBJECT_KEY)
    response = obj.get()
    lines = response[u'Body'].read().decode("utf-8").split("\n")
    csvreader = csv.DictReader(lines)
    for rows in grouper(10, csvreader):
        msg_bodies = []
        for row in rows:
            if row:
                domain_type = row.get('Domain Type').strip()
                if domain_type == 'Federal Agency - Executive':
                    msg_bodies.append(json.dumps(row))
        if msg_bodies:
            send_sqs_messages(msg_bodies)


def main(event, context):
    try:
        get_domains()
        return 200
    except Exception as e:  # pragma: no cover
        log_helper(logger, e, event)
        return
