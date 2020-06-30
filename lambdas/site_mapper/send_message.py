import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
sqs_client = boto3.client('sqs')
SQS_URL = os.getenv('SQS_URL')


def send_message(entry):
    entries = [entry]
    
    try:
        return sqs_client.send_message_batch(
            QueueUrl=SQS_URL,
            Entries=entries
        )

    except ClientError as e:
        err_msg = f'{e} with {e.response}'
        logger.error(err_msg, exc_info=True)
