"""
Tests for eventful_django views module
"""
from __future__ import absolute_import, unicode_literals

import json

from django.test import TestCase

from eventful_django.models import Event, Subscription


class TestEventsEndpoint(TestCase):
    """
    Test for the /events endpoint
    """

    def test_gets_all_events(self):
        Event.objects.create(event_id="HELLO", retry_policy='{"max_retries": 3}')
        response = self.client.get('/events')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), json.loads('{"events": ["HELLO"]}'))

    def test_empty_returns_empty(self):
        response = self.client.get('/events')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b'{"events": []}', response.content)

    def test_post_returns_error_405(self):
        reponse = self.client.post('/events')
        self.assertEqual(reponse.status_code, 405)


class TestSubscriptionEndpoint(TestCase):
    """
    Test for the /subscribe endpoint that manages subscriptions
    """

    def test_creates_subscription(self):
        Event.objects.create(event_id="HELLO", retry_policy='{"max_retries": 3}')
        response = self.client.post('/subscribe', {'event_id': 'HELLO', 'webhook': 'http://gamal.com'})
        resp_json = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp_json["event_id"], "HELLO")
        self.assertEqual(resp_json["webhook"], "http://gamal.com")

    def test_get_request_returns_405(self):
        reponse = self.client.get('/subscribe')
        self.assertEqual(reponse.status_code, 405)

    def test_error_404_when_not_valid_event(self):
        Event.objects.create(event_id="HELLO", retry_policy='{"max_retries": 3}')
        response = self.client.post('/subscribe', {'event_id': 'que?', 'webhook': 'http://gamal.com'})
        self.assertEqual(response.status_code, 404)

    def test_duplicate_webhooks_not_allowed(self):
        new_event = Event.objects.create(event_id="HELLO", retry_policy='{"max_retries": 3}')
        Subscription.objects.create(event=new_event, webhook="http://gamal.com")
        response = self.client.post('/subscribe', {'event_id': 'HELLO', 'webhook': 'http://gamal.com'})
        self.assertEqual(response.status_code, 400)

    def test_error_400_missing_arguments(self):
        Event.objects.create(event_id="HELLO", retry_policy='{"max_retries": 3}')
        response = self.client.post('/subscribe', {'event_id': "HELLO", 'webhook': ''})
        response2 = self.client.post('/subscribe', {'event_id': "HELLO"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response2.status_code, 400)
