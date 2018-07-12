# -*- coding: utf-8 -*-
"""
URLs for eventful_django.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^eventful/events', views.events, name='events'),
    url(r'^eventful/subscribe', views.subscribe, name='subscribe')
]
