"""
Admin dashboard for eventful_django.
Registered models in dhasboard outlined below
"""
from django.contrib import admin

from .models import Event, Subscription


class SubscriptionInLine(admin.TabularInline):
    """
    Subscriptions diplayed in Line.
    """
    model = Subscription


class EventAdmin(admin.ModelAdmin):
    "definition of "
    fieldsets = [('Event Information', {"fields": ['id', 'retry_policy']})]
    inlines = [SubscriptionInLine]


admin.site.register(Event, EventAdmin)
admin.site.register(Subscription)
