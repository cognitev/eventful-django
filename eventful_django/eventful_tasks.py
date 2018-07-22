"""
Celery task for eventful_django
"""
from __future__ import absolute_import, unicode_literals

from os import environ

import requests
from celery import Celery

CELERY_APP = Celery('eventful_tasks', backend=environ.get('EVENTFUL_BROKER_BACKEND', 'amqp'),
                    broker=environ.get('EVENTFUL_BROKER_URL', 'amqp://localhost//'))


@CELERY_APP.task()
def notify(webhook, event, payload):
    """
    notifies webhook by sending it POST request.
    playload sent by caller.
    func is celery task to allow async operation.
    :type webhook: string
    :type event: string
    :type payload: dict
    """
    try:
        response = requests.request('POST', webhook, json={"event": event, "payload": payload})
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        print(error)


@CELERY_APP.task(bind=True)
def debug_task(self):
    """
    debug tasks included with celery
    """
    print('Request: {0!r}'.format(self.request))
