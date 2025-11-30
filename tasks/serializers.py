"""
Serializers for task validation and data handling.
"""
from typing import Dict, List, Any, Tuple
from datetime import datetime


def validate_task(task: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate a single task dictionary.
    Returns (is_valid, error_message, cleaned_task)
    """
    if not isinstance(task, dict):
        return False, "Task must be a dictionary", {}
    
    # Required fields
    if 'title' not in task or not task['title']:
        return False, "Task must have a non-empty 'title'", {}
    
    # Validate and clean due_date
    due_date = task.get('due_date')
    if due_date:
        if isinstance(due_date, str):
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                return False, f"Invalid date format for 'due_date': {due_date}. Use YYYY-MM-DD", {}
    
    # Validate estimated_hours
    estimated_hours = task.get('estimated_hours')
    if estimated_hours is not None:
        try:
            estimated_hours = float(estimated_hours)
            if estimated_hours <= 0:
                return False, "estimated_hours must be greater than 0", {}
        except (ValueError, TypeError):
            return False, "estimated_hours must be a number", {}
    else:
        estimated_hours = 8  # Default
    
    # Validate importance
    importance = task.get('importance')
    if importance is not None:
        try:
            importance = int(importance)
            if not (1 <= importance <= 10):
                return False, "importance must be between 1 and 10", {}
        except (ValueError, TypeError):
            return False, "importance must be an integer between 1 and 10", {}
    else:
        importance = 5  # Default
    
    # Validate dependencies
    dependencies = task.get('dependencies', [])
    if not isinstance(dependencies, list):
        return False, "dependencies must be a list", {}
    
    # Clean task
    cleaned_task = {
        'title': str(task['title']).strip(),
        'due_date': due_date,
        'estimated_hours': estimated_hours,
        'importance': importance,
        'dependencies': [int(d) if isinstance(d, (int, str)) and str(d).isdigit() else d for d in dependencies],
        'id': task.get('id', task.get('title'))  # Use title as fallback ID
    }
    
    return True, "", cleaned_task


def validate_tasks(tasks: List[Dict[str, Any]]) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Validate a list of tasks.
    Returns (is_valid, error_message, cleaned_tasks)
    """
    if not isinstance(tasks, list):
        return False, "Tasks must be a list", []
    
    if len(tasks) == 0:
        return False, "Tasks list cannot be empty", []
    
    cleaned_tasks = []
    for idx, task in enumerate(tasks):
        is_valid, error_msg, cleaned_task = validate_task(task)
        if not is_valid:
            return False, f"Task {idx + 1}: {error_msg}", []
        cleaned_tasks.append(cleaned_task)
    
    return True, "", cleaned_tasks

