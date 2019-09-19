"""
Celery task for eventful_django
"""
from __future__ import absolute_import, unicode_literals

from os import environ
from celery import Celery

CELERY_APP = Celery('eventful_tasks',
                    backend=environ.get('EVENTFUL_BROKER_BACKEND', 'amqp'),
                    broker=environ.get('EVENTFUL_BROKER_URL',
                                       'amqp://localhost//'))


@CELERY_APP.task()
def notify(hook, event, payload, headers, subscription_model):
    """
    notifies webhook/topic by sending it POST request/message.
    playload sent by caller.
    func is celery task to allow async operation.
    :type webhook: string
    :type event: string
    :type payload: dict
    """
    subscription_model.notify(hook, event, payload, headers)


@CELERY_APP.task(bind=True)
def debug_task(self):
    """
    debug tasks included with celery
    """
    print('Request: {0!r}'.format(self.request))
