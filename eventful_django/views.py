# -*- coding: utf-8 -*-
"""
Views (endpoints) for eventful_django.
"""
from django.db import IntegrityError
from django.http import JsonResponse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from .models import Event, Subscription


@csrf_exempt
def events(request):
    """get all events - events endpoint
    Only GET requests are allowed.
    Event creating is limited to admin dashboard.
    """
    if request.method == 'GET':
        all_events = list(Event.objects.values('event_id').all())
        all_events_formated = [entries['event_id'] for entries in all_events]
        return JsonResponse({'events': all_events_formated}, safe=False)
    return JsonResponse({}, status=405)


@csrf_exempt
def subscribe(request):
    """
    create a subscription to an event.
    Only POST requests are allowed.
    :param request: post req with valid event & webhook.
    :type request: request
    :rtype: respoonse
    """
    if request.method == 'POST':
        try:
            event = Event.objects.get(pk=request.POST['event_id'])
            if request.POST['webhook'] == '':
                return JsonResponse({}, status=400)
            new_sub = Subscription(webhook=request.POST['webhook'], event_id=event.event_id)
            new_sub.save()
            return JsonResponse({"event_id": new_sub.event.event_id, "webhook": new_sub.webhook})
        except Event.DoesNotExist as error:
            return JsonResponse({}, status=404)
        except MultiValueDictKeyError as error:
            return JsonResponse({}, status=400)
        except IntegrityError as error:
            if 'UNIQUE constraint failed' in str(error.__cause__):
                return JsonResponse({}, status=400)
            print(error)
            return JsonResponse({}, status=500)
    return JsonResponse({}, status=405)
