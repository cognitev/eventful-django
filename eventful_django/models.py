# -*- coding: utf-8 -*-
"""
Database models for eventful_django.
"""
from __future__ import absolute_import, unicode_literals

import json

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from .eventful_tasks import notify


@python_2_unicode_compatible
class Subscription(models.Model):
    """
    Subscription represents a webhook to event assignment
    """
    webhook = models.URLField('Web Hook URL')
    event = models.ForeignKey("eventful_django.Event", on_delete=models.CASCADE)
    headers = models.TextField('Request Headers', null=True)

    class Meta:
        unique_together = (("webhook", "event"))

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return self.webhook


class Event(models.Model):
    """
    Event that is emitted once it occurs.
    Event is emitted by sending POST requests to subscription webhook
    """
    event_id = models.CharField('Event ID', primary_key=True, max_length=200)
    retry_policy = models.TextField('Retry Policy')

    @classmethod
    def dispatch(cls, evt_id, payload):
        """
        Notifies subscribers of event_id with payload.
        :type evt_id: string
        :param payload: payload to send to subscribers
        :type payload: dict
        """
        evt = Event.objects.get(pk=evt_id)
        evt.notify_subscribers(payload)

    def notify_subscribers(self, payload):
        """
        Notifies subscriptions async via celery
        task notify. Payload sent to all.
        """
        for subscription in self.subscription_set.all():
            headers = eval(subscription.headers or '{}')
            try:
                notify.apply_async(
                    (subscription.webhook, self.event_id, payload, headers),
                    retry=True,
                    retry_policy=json.loads(self.retry_policy),
                )
            except notify.OperationalError as notification_error:
                print(notification_error)

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return self.event_id
