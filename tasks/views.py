import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from datetime import date

from .scoring import analyze_and_sort_tasks, detect_circular_dependencies
from .serializers import validate_tasks


@csrf_exempt
@require_http_methods(["POST"])
def analyze_tasks(request):
    """
    POST /api/tasks/analyze/
    Accept a list of tasks and return them sorted by priority score.
    
    Request body:
    {
        "tasks": [
            {
                "title": "Fix login bug",
                "due_date": "2025-11-30",
                "estimated_hours": 3,
                "importance": 8,
                "dependencies": []
            }
        ],
        "strategy": "smart_balance",  // optional: "fastest_wins", "high_impact", "deadline_driven", "smart_balance"
        "weights": {  // optional: custom weights
            "urgency": 0.4,
            "importance": 0.3,
            "effort": 0.2,
            "dependencies": 0.1
        }
    }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return JsonResponse({'error': 'Invalid JSON format', 'details': str(e)}, status=400)
    
    tasks = payload.get('tasks')
    strategy = payload.get('strategy', 'smart_balance')
    weights = payload.get('weights')
    
    if not tasks:
        return JsonResponse({'error': 'Missing required field: tasks'}, status=400)
    
    # Validate tasks
    is_valid, error_msg, cleaned_tasks = validate_tasks(tasks)
    if not is_valid:
        return JsonResponse({'error': error_msg}, status=400)
    
    # Validate strategy
    valid_strategies = ['fastest_wins', 'high_impact', 'deadline_driven', 'smart_balance']
    if strategy not in valid_strategies:
        return JsonResponse({
            'error': f'Invalid strategy. Must be one of: {", ".join(valid_strategies)}'
        }, status=400)
    
    # Validate weights if provided
    if weights:
        if not isinstance(weights, dict):
            return JsonResponse({'error': 'weights must be a dictionary'}, status=400)
        
        required_keys = ['urgency', 'importance', 'effort', 'dependencies']
        if not all(key in weights for key in required_keys):
            return JsonResponse({
                'error': f'weights must contain all keys: {", ".join(required_keys)}'
            }, status=400)
        
        # Validate weight values are numbers and sum to ~1.0
        try:
            weight_values = [float(weights[key]) for key in required_keys]
            weight_sum = sum(weight_values)
            if not (0.9 <= weight_sum <= 1.1):  # Allow small floating point errors
                return JsonResponse({
                    'error': f'weights must sum to approximately 1.0 (current sum: {weight_sum})'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'All weight values must be numbers'}, status=400)
    
    try:
        # Analyze and sort tasks
        sorted_tasks = analyze_and_sort_tasks(
            cleaned_tasks,
            strategy=strategy,
            weights=weights,
            current_date=date.today()
        )
        
        # Check for circular dependencies
        cycles = detect_circular_dependencies(cleaned_tasks)
        warnings = []
        if cycles:
            warnings.append(f"Warning: {len(cycles)} circular dependency cycle(s) detected")
        
        return JsonResponse({
            'tasks': sorted_tasks,
            'strategy_used': strategy,
            'total_tasks': len(sorted_tasks),
            'warnings': warnings
        })
    
    except Exception as e:
        return JsonResponse({
            'error': 'Error analyzing tasks',
            'details': str(e)
        }, status=400)


@require_http_methods(["GET"])
def suggest_tasks(request):
    """
    GET /api/tasks/suggest/
    Return the top 3 tasks the user should work on today, with explanations.
    
    Query parameters:
    - strategy: optional, same as analyze endpoint
    - limit: optional, number of suggestions (default: 3)
    
    Note: This endpoint expects tasks to be stored or passed differently.
    For this implementation, we'll use a session-based approach or require
    tasks to be sent via query params. For simplicity, we'll return a message
    indicating tasks should be analyzed first.
    """
    strategy = request.GET.get('strategy', 'smart_balance')
    limit = int(request.GET.get('limit', 3))
    
    # In a real application, tasks would be stored in a database
    # For this implementation, we'll return instructions
    return JsonResponse({
        'message': 'Use POST /api/tasks/analyze/ to analyze your tasks first, then take the top results.',
        'suggestion': f'To get suggestions, analyze your tasks using the /api/tasks/analyze/ endpoint with strategy="{strategy}", then take the top {limit} results.',
        'example': {
            'endpoint': '/api/tasks/analyze/',
            'method': 'POST',
            'body': {
                'tasks': [
                    {
                        'title': 'Example task',
                        'due_date': '2025-12-01',
                        'estimated_hours': 2,
                        'importance': 8,
                        'dependencies': []
                    }
                ],
                'strategy': strategy
            }
        }
    })


def index(request):
    """
    Serve the frontend HTML page.
    """
    return render(request, 'tasks/index.html')
