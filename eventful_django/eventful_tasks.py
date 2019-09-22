"""
Celery task for eventful_django
"""
from __future__ import absolute_import, unicode_literals

from os import environ

import requests
from celery import Celery
from google.cloud import pubsub_v1
import json

CELERY_APP = Celery('eventful_tasks',
                    backend=environ.get('EVENTFUL_BROKER_BACKEND', 'amqp'),
                    broker=environ.get('EVENTFUL_BROKER_URL',
                                       'amqp://localhost//'))
PROJECT_ID = environ.get('GOOGLE_PROJECT_ID', 'cogni-sandbox')


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
        print(error)


@CELERY_APP.task()
def notify_pubsub(topic, event, payload, headers):
    """
    notifies topics by publsihing on it.
    playload sent by caller.
    func is celery task to allow async operation.
    :type topic: string
    :type event: string
    :type payload: dict
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, topic)
    payload_string = json.dumps(payload).encode('utf-8')
    publisher.publish(topic_path, data=payload_string)


@CELERY_APP.task(bind=True)
def debug_task(self):
    """
    debug tasks included with celery
    """
    print('Request: {0!r}'.format(self.request))
