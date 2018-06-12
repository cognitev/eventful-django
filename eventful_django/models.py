# -*- coding: utf-8 -*-
"""
Database models for eventful_django.
"""

import requests

from __future__ import absolute_import, unicode_literals

from django.db import models
from datatime import datetime
from django.utils.encoding import python_2_unicode_compatible

from model_utils.models import TimeStampedModel


@python_2_unicode_compatible
class Subscription(TimeStampedModel):
    """
    Subscription represents a webhook to event assignment
    """

    webhook = models.URLField('Web Hook URL')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)


    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return '<Subscription: {} -> {}>'.format(self.event_id, self.webhook)


@python_2_unicode_compatible
class Execution(TimeStampedModel):
    """
    This model represents executions for event triggering
    """

    status_choices = [
                      ('Succeeded','succeeded'),
                      ('Failed','failed'),
                      ('Pending','pending'),
                     ]

    status = models.CharField(choices=self.status_choices)
    payload = models.TextField('Event Payload')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return '<[{}] Execution: {}>'.format(self.status, self.subscription)

class Event(models.Model):
    id = models.CharField('Event ID', primary_key=True)
    max_retries = models.IntegerField('Maximum Number of retries')
    first_retry_interval = models.FloatField('Number of seconds before first retry', default=3)
    retry_interval = models.FloatField('Number of seconds between retries', default=1)
    interval_max = models.FloatField('Maximum number of seconds to wait between retries', default=1)

    @classmethod
    def dispatch(cls, evt_id, payload):
        evt = Event.objects.get(pk=evt_id)
        evt.notify_subscribers(payload)

    @classmethod
    def notify(webhook, event_id, payload, exec_id):
        exec = Execution.objects.get(pk=exec_id).update(status='failed')
        try:
            response = requests.request('POST', webhook, json=payload)
            response.raise_for_status()
            exec.update('succeeded')
        except requests.exceptions.HTTPError as error:
            exec.update(status='failed')
            exec.save()




    def notify_subscribers(self, payload):
        for subscription in self.subscriptions:
            exec = Execution.objects.create(subscription=subscription, status='pending', payload=payload)
            try:
                self.notify.apply_async((subscription.webhook, self.id, payload, exec.id), retry=True, retry_policy={
                    'max_retries': self.max_retries,
                    'interval_start': self.first_retry_interval,
                    'interval_step': self.retry_interval,
                    'interval_max': self.interval_max,
                })
            except self.notify.OperationalError as notification_error:
                exec.update(status='failed')
                exec.save()

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return '<Event: {}>'.format(self.id)



