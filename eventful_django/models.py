# -*- coding: utf-8 -*-
"""
Database models for eventful_django.
"""
from __future__ import absolute_import, unicode_literals

import json
import logging
from itertools import chain

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from .eventful_tasks import notify, notify_pubsub

LOGGER = logging.getLogger(__name__)


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

    def notify(self, event, payload, retry_policy):
        """
        Start Notify Job for specified url hook
        """
        headers = eval(self.headers or "{}")  # pylint: disable=eval-used
        notify.apply_async(
            (self.webhook, event, payload, headers),
            retry=True,
            retry_policy=json.loads(retry_policy),
        )


@python_2_unicode_compatible
class SubscriptionPubSub(models.Model):
    """
    Subscription represents a topic to event assignment
    """
    topic = models.CharField(max_length=100)
    event = models.ForeignKey("eventful_django.Event", on_delete=models.CASCADE)
    gcp_project_id = models.CharField(max_length=100, default="extended-web-217714")

    class Meta:
        unique_together = (("topic", "event"))

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return self.topic

    def notify(self, event, payload, retry_policy):  # pylint: disable=unused-argument
        """
        Start Notify Job for pubsub
        """
        notify_pubsub.apply_async(
            (self.gcp_project_id, self.topic, payload),
            retry=True,
            retry_policy=json.loads(retry_policy),
        )


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
        subscriptions = list(chain(self.subscription_set.all(), self.subscriptionpubsub_set.all()))

        for subscription in subscriptions:
            try:
                subscription.notify(self.event_id, payload, self.retry_policy)
            except notify.OperationalError as notification_error:
                LOGGER.exception("Error {} while notifing subscripers for event {} with payload {}".format(
                    notification_error, self.event_id, payload))

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return self.event_id
