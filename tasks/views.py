import json 
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render

@csrf_exempt 
@require_http_methods(["POST"])
def analyze_tasks(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid JSON'}), content_type = 'application/json')
    
    tasks = payload.get('tasks')
    strategy = payload.get("strategy", "smart")
    weights = payload.get('weights')

    if not isinstance(tasks, list):
        return HttpResponseBadRequest(json.dumps({'error': ''}))



