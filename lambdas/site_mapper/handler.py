import json
import logging
import os
import sys

from spider import scrape


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(asctime)s: %(message)s'
)


def log_helper(logger, e, event):
    logger.critical('## EXCEPTION')
    logger.critical(e, exc_info=True)
    logger.critical('## EVENT')
    logger.critical(event)


def main(event, context):
    
    body = json.loads(event['Records'][0]['body'])
    
    try:
        scrape(**body)
    except Exception as e:
        log_helper(logger, e, event)
        sys.exit(1)
    # Without the sys.exit, subsequent executions raise ReactorNotRestartable
    # TODO: figure out how to reuse reactor across executions
    sys.exit(0)