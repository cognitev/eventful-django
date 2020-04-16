"""
Celery task for eventful_django
"""
from __future__ import absolute_import, unicode_literals

import json
import logging
from os import environ

import requests

from celery import Celery
from google.cloud import pubsub_v1

LOGGER = logging.getLogger(__name__)

# Make sure that EVENTFUL BROKER URL is provided
assert "EVENTFUL_BROKER_URL" in environ, "EVENTFUL_BROKER_URL env is not exist in environment variables"

# Removing CELERY native envs, as celery respect these envs even if EVENTFUL envs are exist
environ.pop("CELERY_BROKER_URL", None)
environ.pop("CELERY_RESULT_BACKEND", None)

BROKER_URL = environ["EVENTFUL_BROKER_URL"]
RESULT_BACKEND = environ.get("EVENTFUL_RESULT_BACKEND")

# celery queue will be used if no queue is provided
DEFAULT_QUEUE = environ.get("EVENTFUL_DEFAULT_QUEUE", "celery")

LOGGER.info("Eventful broker url is {}".format(BROKER_URL))
LOGGER.info("Eventful default queue is {}".format(DEFAULT_QUEUE))
LOGGER.info("Eventful result backend is {}".format(RESULT_BACKEND))

TASK_IGNORE_RESULT = False
if RESULT_BACKEND is None:
    LOGGER.warning("EVENTFUL_RESULT_BACKEND env is not exist in environment variables, " +
                   "eventful results won't be stored")
    TASK_IGNORE_RESULT = True

CELERY_APP = Celery('eventful_tasks',
                    broker=BROKER_URL,
                    backend=RESULT_BACKEND)

CELERY_APP.conf.task_default_queue = DEFAULT_QUEUE
CELERY_APP.conf.task_ignore_result = TASK_IGNORE_RESULT


@CELERY_APP.task()
def notify(webhook, event, payload, headers):
    """
    notifies webhook by sending it POST request.
    playload sent by caller.
    func is celery task to allow async operation.
    :type webhook: string
    :type event: string
    :type payload: dict
    """
    try:
        response = requests.request(
            'POST',
            webhook,
            json={
                "event": event,
                "payload": payload
            },
            headers=headers,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        LOGGER.exception(
            "Error {} while sending http request to url {} with payload {} with headers {} for event {}".
            format(error, webhook, payload, headers, event))


@CELERY_APP.task()
def notify_pubsub(gcp_project_id, topic, payload):
    """
    notifies topics by publsihing on it.
    playload sent by caller.
    func is celery task to allow async operation.
    :type topic: string
    :type event: string
    :type payload: dict
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(gcp_project_id, topic)  # pylint: disable=no-member
    payload_string = json.dumps(payload).encode('utf-8')
    publisher.publish(topic_path, data=payload_string)


@CELERY_APP.task(bind=True)
def debug_task(self):
    """
    debug tasks included with celery
    """
    LOGGER.info('Request: {0!r}'.format(self.request))
