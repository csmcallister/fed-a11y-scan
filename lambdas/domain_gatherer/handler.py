import logging
import os

from utils.get_domains import get_domains

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR,
                    format='%(levelname)s: %(asctime)s: %(message)s')


def log_helper(logger, e, event):
    logger.error('## EXCEPTION')
    logger.error(e, exc_info=True)
    logger.error('## ENV VARS')
    logger.error(os.environ)
    logger.error('## EVENT')
    logger.error(event)


def main(event, context):
    try:
        get_domains()
    except Exception as e:
        log_helper(logger, e, event)
        return
