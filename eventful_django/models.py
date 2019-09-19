# -*- coding: utf-8 -*-
"""
Database models for eventful_django.
"""
from __future__ import absolute_import, unicode_literals

import json

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from os import environ
from .eventful_tasks import notify
import requests
from google.cloud import pubsub_v1

PROJECT_ID = environ.get('GOOGLE_PROJECT_ID', 'cogni-sandbox')


@python_2_unicode_compatible
class Subscription(models.Model):
    """
    Subscription represents a webhook to event assignment
    """
    webhook = models.URLField('Web Hook URL')
    event = models.ForeignKey("eventful_django.Event",
                              on_delete=models.CASCADE)
    headers = models.TextField('Request Headers', null=True)

    class Meta:
        unique_together = (("webhook", "event"))

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return self.webhook

    def notify(self, webhook, event, payload, headers):
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


@python_2_unicode_compatible
class SubscriptionPubSub(models.Model):
    """
    Subscription represents a topic to event assignment
    """
    topic = models.CharField(max_length=100)
    event = models.ForeignKey("eventful_django.Event",
                              on_delete=models.CASCADE)
    headers = models.TextField('Request Headers', null=True)

    class Meta:
        unique_together = (("topic", "event"))

    def __str__(self):
        """
        Get a string representation of this model instance.
        """
        return self.topic

    def notify(self, topic, event, payload, headers):
        """
        notifies topics by publsihing on it.
        playload sent by caller.
        func is celery task to allow async operation.
        :type topic: string
        :type event: string
        :type payload: dict
        """
        try:
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, topic)
            payload_string = json.dumps(payload).encode('utf-8')
            publisher.publish(topic_path, data=payload_string)
        except Exception as e:
            print(e)


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
                    (subscription.webhook, self.event_id, payload, headers,
                     subscription),
                    retry=True,
                    retry_policy=json.loads(self.retry_policy),
                )
            except notify.OperationalError as notification_error:
                print(notification_error)

        for subscription in self.subscriptionpubsub_set.all():
            headers = eval(subscription.headers or '{}')
            try:
                notify.apply_async(
                    (subscription.topic, self.event_id, payload, headers,
                     subscription),
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
