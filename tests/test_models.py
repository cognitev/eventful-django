"""
Tests for the `eventful-django` models module.
"""
from __future__ import absolute_import, unicode_literals

import json

from django.test import TestCase

import mock
from eventful_django.eventful_tasks import notify_pubsub
from eventful_django.models import Event, Subscription

APPLY_ASYNC = mock.Mock()


class TestEventDispatch(TestCase):
    """
    Testing event notification dispatching
    """
    @mock.patch("eventful_django.eventful_tasks.pubsub_v1")
    def test_pubsub_event_trigger(self, pubsub_mock):
        client_mock = mock.Mock()
        pubsub_mock.PublisherClient = client_mock
        publish_mock = mock.Mock()
        client_mock.publish = publish_mock
        topic = "test_topic"
        gcp_project_id = "gcp_project_id"
        payload = {}
        notify_pubsub(gcp_project_id, topic, payload)
        self.assertEqual(client_mock.call_count, 1)
        client_mock.assert_called_with()

    @mock.patch("eventful_django.eventful_tasks.notify.apply_async",
                side_effect=APPLY_ASYNC)
    def test_firing_event_notifies_subscribers(self, req_mock):
        new_event = Event(event_id="HELLO", retry_policy='{"max_retries": 3}')
        new_event.save()

        new_subscriber = Subscription(webhook="http://gamal.com",
                                      event=new_event)
        new_subscriber.save()

        Event.dispatch("HELLO", {"foo": "bar"})
        self.assertEqual(req_mock.call_count, 1)
        req_mock.assert_called_with(
            (
                new_subscriber.webhook,
                new_event.event_id,
                {
                    "foo": "bar"
                },
                {},
            ),
            retry=True,
            retry_policy=json.loads(new_event.retry_policy),
        )

    @mock.patch("eventful_django.eventful_tasks.notify.apply_async",
                side_effect=APPLY_ASYNC)
    def test_firing_event_notifies_all_subscribers(self, req_mock):
        new_event = Event(event_id="HELLO", retry_policy='{"max_retries": 3}')
        new_event.save()

        new_subscriber = Subscription(webhook="http://gamal.com",
                                      event=new_event)
        new_subscriber.save()

        new_subscriber = Subscription(webhook="http://ahmed.com",
                                      event=new_event)
        new_subscriber.save()

        new_subscriber = Subscription(webhook="http://wtf.com",
                                      event=new_event)
        new_subscriber.save()

        Event.dispatch("HELLO", {"foo": "bar"})
        self.assertEqual(req_mock.call_count, 3)
        req_mock.assert_called_with(
            (
                new_subscriber.webhook,
                new_event.event_id,
                {
                    "foo": "bar"
                },
                {},
            ),
            retry=True,
            retry_policy=json.loads(new_event.retry_policy),
        )

    @mock.patch("eventful_django.eventful_tasks.notify.apply_async",
                side_effect=APPLY_ASYNC)
    def test_firing_event_notifies_all_subscribers_different_events(
            self, req_mock):
        new_event = Event(event_id="HELLO", retry_policy='{"max_retries": 3}')
        new_event.save()

        new_subscriber = Subscription(webhook="http://gamal.com",
                                      event=new_event)
        new_subscriber.save()

        new_subscriber = Subscription(webhook="http://ahmed.com",
                                      event=new_event)
        new_subscriber.save()

        new_event2 = Event(event_id="BORED",
                           retry_policy='{"max_retries": 10}')
        new_event2.save()

        new_subscriber2 = Subscription(webhook="http://wtf.com",
                                       event=new_event2)
        new_subscriber2.save()

        Event.dispatch("HELLO", {"foo": "bar"})
        self.assertEqual(req_mock.call_count, 2)
        req_mock.assert_called_with(
            (
                new_subscriber.webhook,
                new_event.event_id,
                {
                    "foo": "bar"
                },
                {},
            ),
            retry=True,
            retry_policy=json.loads(new_event.retry_policy),
        )

    @mock.patch("eventful_django.eventful_tasks.notify.apply_async",
                side_effect=APPLY_ASYNC)
    def test_firing_event_notifies_subscribers_with_headers(self, req_mock):
        new_event = Event(event_id="HELLO", retry_policy='{"max_retries": 3}')
        new_event.save()

        new_subscriber = Subscription(webhook="http://gamal.com",
                                      event=new_event,
                                      headers={'test': 'headers'})
        new_subscriber.save()

        Event.dispatch("HELLO", {"foo": "bar"})
        self.assertEqual(req_mock.call_count, 1)
        req_mock.assert_called_with(
            (
                new_subscriber.webhook,
                new_event.event_id,
                {
                    "foo": "bar"
                },
                {
                    'test': 'headers'
                },
            ),
            retry=True,
            retry_policy=json.loads(new_event.retry_policy),
        )

    @mock.patch("eventful_django.models.Subscription.generate_jwt_token", return_value='token')
    @mock.patch("eventful_django.eventful_tasks.notify.apply_async",
                side_effect=APPLY_ASYNC)
    def test_firing_event_notifies_subscribers_cloud_function(self, req_mock, token_mock):
        new_event = Event(event_id="HELLO", retry_policy='{"max_retries": 3}')
        new_event.save()

        new_subscriber = Subscription(webhook="http://gamal.com",
                                      event=new_event,
                                      headers={'test': 'test'},
                                      is_cloud_function=True,
                                      client_email='test',
                                      token_uri='www.test.uri',
                                      private_key='private')
        new_subscriber.save()

        Event.dispatch("HELLO", {"foo": "bar"})
        self.assertEqual(req_mock.call_count, 1)
        self.assertEqual(token_mock.call_count, 1)
        req_mock.assert_called_with(
            (
                new_subscriber.webhook,
                new_event.event_id,
                {
                    "foo": "bar"
                },
                {
                    'test': 'test',
                    'Authorization': 'Bearer token'
                },
            ),
            retry=True,
            retry_policy=json.loads(new_event.retry_policy),
        )

    @mock.patch("eventful_django.models.Subscription.generate_jwt_token", return_value='token')
    @mock.patch("eventful_django.eventful_tasks.notify.apply_async",
                side_effect=APPLY_ASYNC)
    def test_firing_event_notifies_subscribers_no_cloud_function(self, req_mock, token_mock):
        new_event = Event(event_id="HELLO", retry_policy='{"max_retries": 3}')
        new_event.save()

        new_subscriber = Subscription(webhook="http://gamal.com",
                                      event=new_event,
                                      headers={'test': 'test'},
                                      is_cloud_function=False,
                                      client_email='test',
                                      token_uri='www.test.uri',
                                      private_key='private')
        new_subscriber.save()

        Event.dispatch("HELLO", {"foo": "bar"})
        self.assertEqual(req_mock.call_count, 1)
        self.assertEqual(token_mock.call_count, 0)
        req_mock.assert_called_with(
            (
                new_subscriber.webhook,
                new_event.event_id,
                {
                    "foo": "bar"
                },
                {
                    'test': 'test',
                },
            ),
            retry=True,
            retry_policy=json.loads(new_event.retry_policy),
        )
