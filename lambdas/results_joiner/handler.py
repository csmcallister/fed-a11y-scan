import asyncio
from datetime import datetime
import json
import logging
import os

from utils import s3_utils

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(asctime)s: %(message)s'
)

RESULTS_BUCKET_NAME = os.getenv('RESULTS_BUCKET_NAME')
DATA_BUCKET_NAME = os.getenv('DATA_BUCKET_NAME')

now = datetime.now().strftime("%Y-%m-%d")


def log_helper(logger, e, event):
    logger.error('## EXCEPTION')
    logger.error(e, exc_info=True)
    logger.error('## EVENT')
    logger.error(event)


def main(event, context):
    # Aggregate scan results
    keys = s3_utils.get_matching_s3_keys(RESULTS_BUCKET_NAME, suffix='.json')
    try:
        data = asyncio.run(s3_utils.bulk_read(RESULTS_BUCKET_NAME, keys))
    except Exception as e:
        log_helper(logger, e, event)
        return
    
    # Put json file for all of the data
    try:
        s3_utils.put_object(data, DATA_BUCKET_NAME, 'data.json')
    except Exception as e:
        log_helper(logger, e, event)
        return
    
    # Calculate the number of accessible domains
    n_accessible = 0
    for d in data:
        n_issues = len(json.loads(d.get('issues', {})).get('issues', []))
        if not n_issues:
            n_accessible += 1
    aggregate_data = [{now: n_accessible / len(data)}]
    
    # Combine historical data with the most recent snapshot, write it
    historical_data_key = s3_utils.partial_key_exists(
        'hist.json',
        DATA_BUCKET_NAME
    )
    
    if historical_data_key:
        historical_data = s3_utils.read_object(
            historical_data_key,
            DATA_BUCKET_NAME
        )
        historical_data.extend(aggregate_data)    
        s3_utils.put_object(historical_data, DATA_BUCKET_NAME, 'hist.json')
    
    else:
        # History doesn't exist, so create it
        s3_utils.put_object(aggregate_data, DATA_BUCKET_NAME, 'hist.json')
