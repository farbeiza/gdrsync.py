#!/usr/bin/python

import logging
import random
import time

RETRIES = 5

LOGGER = logging.getLogger(__name__)

def execute(request):
    for retry in range(RETRIES):
        try:
            return request()
        except:
            wait = exponentialBackoffWait(retry)
            LOGGER.exception('Retry %d failed. Retrying after %f s...', retry,
                    wait)

            time.sleep(wait)

    raise RuntimeError('Request aborted after %d retries.' % RETRIES)

def exponentialBackoffWait(retry):
    return (2 ** retry) + random.random()
