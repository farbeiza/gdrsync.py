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
            LOGGER.exception("Retry %(retry)d failed. Retrying after %(wait)f s...",
                    {'retry': retry, 'wait': wait});

            time.sleep(wait);

    raise RuntimeError('Request aborted after %(retries)d retries.'
            % {'retries' : RETRIES})

def exponentialBackoffWait(retry):
    return (2 ** retry) + random.random()
