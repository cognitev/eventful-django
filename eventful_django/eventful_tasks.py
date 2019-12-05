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

CELERY_APP = Celery('eventful_tasks',
                    backend=environ.get('EVENTFUL_BROKER_BACKEND', 'amqp'),
                    broker=environ.get('EVENTFUL_BROKER_URL', 'amqp://localhost//'))


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
