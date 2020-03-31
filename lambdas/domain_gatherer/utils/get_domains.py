import csv
from itertools import zip_longest
import json
import logging
import os

logger = logging.getLogger(__name__)

BUCKET_NAME = os.getenv('BUCKET_NAME')
OBJECT_KEY = os.getenv('OBJECT_KEY')
SQS_URL = os.getenv('SQS_URL')

if BUCKET_NAME:
    import boto3
    from botocore.exceptions import ClientError
    sqs_client = boto3.client('sqs')


def grouper(n, iterable, fillvalue=None):
    '''Group iterable into batches of n items, e.g. to send 10 items to SQS.'''
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def send_sqs_messages(msg_bodies, sqs_queue_url=SQS_URL):
    entries = []
    for i, msg_body in enumerate(msg_bodies):
        if msg_body:
            entries.append({'Id': str(i), 'MessageBody': msg_body})
        else:
            break
    
    try:
        _ = sqs_client.send_message_batch(
            QueueUrl=sqs_queue_url,
            Entries=entries)
    except ClientError as e:
        err_msg = f'{e} with {e.response}'
        logger.error(err_msg, exc_info=True)


def get_domains():
    if BUCKET_NAME:
        s3 = boto3.resource(u's3')
        bucket = s3.Bucket(BUCKET_NAME)
        obj = bucket.Object(key=OBJECT_KEY)
        response = obj.get()
        lines = response[u'Body'].read().decode("utf-8").split("\n")
        csvreader = csv.DictReader(lines)
        for rows in grouper(10, csvreader):
            msg_bodies = []
            for row in rows:
                if not row:
                    continue
                # nix non-Executive branch domains for now
                domain_type = row.get('Domain Type').strip()
                if domain_type == 'Federal Agency - Executive':
                    msg_bodies.append(json.dumps(row))
            if not msg_bodies:
                continue
            send_sqs_messages(msg_bodies)
    else:
        # for local testing
        with open('../../../domains/domains.csv', 'r') as f:
            lines = f.read().split("\n")
        csvreader = csv.DictReader(lines)
        for i, row in enumerate(csvreader):
            if i == 0:
                _ = json.dumps(row)
            else:
                break
         
    return "Success!"
        

if __name__ == '__main__':
    _ = get_domains()
