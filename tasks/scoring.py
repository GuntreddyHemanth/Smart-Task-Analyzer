"""
Priority scoring algorithm for task management.
Handles multiple scoring strategies and calculates priority scores based on:
- Urgency (due date)
- Importance (1-10 scale)
- Effort (estimated hours)
- Dependencies (blocking other tasks)
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Set
import math


def detect_circular_dependencies(tasks: List[Dict]) -> List[List[int]]:
    """
    Detect circular dependencies in a list of tasks.
    Returns a list of cycles found (each cycle is a list of task indices).
    """
    cycles = []
    n = len(tasks)
    
    # Build dependency graph
    graph = {i: set(tasks[i].get('dependencies', [])) for i in range(n)}
    
    # DFS to detect cycles
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(node: int) -> bool:
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return True
        
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        # Visit dependencies
        for dep_id in graph[node]:
            # Find task index by ID
            dep_idx = None
            for idx, task in enumerate(tasks):
                if task.get('id') == dep_id or idx == dep_id:
                    dep_idx = idx
                    break
            
            if dep_idx is not None and dep_idx < n:
                dfs(dep_idx)
        
        rec_stack.remove(node)
        path.pop()
        return False
    
    for i in range(n):
        if i not in visited:
            dfs(i)
    
    return cycles


def calculate_urgency_score(due_date: Optional[str], current_date: Optional[date] = None) -> float:
    """
    Calculate urgency score based on due date.
    - Past due dates get high urgency (exponential increase)
    - Near future dates get moderate urgency
    - Far future dates get low urgency
    
    Returns a score between 0 and 100.
    """
    if not due_date:
        return 0.0
    
    if current_date is None:
        current_date = date.today()
    
    try:
        if isinstance(due_date, str):
            due = datetime.strptime(due_date, '%Y-%m-%d').date()
        else:
            due = due_date
    except (ValueError, TypeError):
        return 0.0
    
    days_until_due = (due - current_date).days
    
    if days_until_due < 0:
        # Past due - exponential penalty
        days_overdue = abs(days_until_due)
        return min(100.0, 50.0 + (days_overdue * 5))
    elif days_until_due == 0:
        # Due today
        return 90.0
    elif days_until_due <= 1:
        # Due tomorrow
        return 80.0
    elif days_until_due <= 3:
        # Due in 2-3 days
        return 70.0
    elif days_until_due <= 7:
        # Due in a week
        return 50.0
    elif days_until_due <= 14:
        # Due in 2 weeks
        return 30.0
    elif days_until_due <= 30:
        # Due in a month
        return 15.0
    else:
        # Far future
        return max(5.0, 30.0 - (days_until_due / 10))


def calculate_importance_score(importance: int) -> float:
    """
    Convert importance rating (1-10) to a score (0-100).
    """
    if not isinstance(importance, (int, float)):
        return 0.0
    
    importance = max(1, min(10, int(importance)))
    return (importance / 10.0) * 100.0


def calculate_effort_score(estimated_hours: float) -> float:
    """
    Calculate effort score - lower effort tasks get higher scores (quick wins).
    Returns a score between 0 and 100.
    """
    if not isinstance(estimated_hours, (int, float)) or estimated_hours <= 0:
        return 0.0
    
    # Inverse relationship: lower hours = higher score
    # Using logarithmic scale to prevent extremely high scores for very small tasks
    if estimated_hours <= 1:
        return 100.0
    elif estimated_hours <= 2:
        return 90.0
    elif estimated_hours <= 4:
        return 75.0
    elif estimated_hours <= 8:
        return 60.0
    elif estimated_hours <= 16:
        return 40.0
    else:
        return max(10.0, 50.0 - (estimated_hours / 2))


def calculate_dependency_score(task: Dict, all_tasks: List[Dict], task_index: int) -> float:
    """
    Calculate dependency score - tasks that block other tasks get higher priority.
    Returns a score between 0 and 100.
    """
    blocking_count = 0
    
    # Check how many tasks depend on this one
    task_id = task.get('id', task_index)
    
    for other_task in all_tasks:
        other_deps = other_task.get('dependencies', [])
        # Check if this task is in other task's dependencies
        if task_id in other_deps or task_index in other_deps:
            blocking_count += 1
    
    # Score increases with number of blocked tasks (capped at 100)
    return min(100.0, blocking_count * 20.0)


def calculate_priority_score(
    task: Dict,
    all_tasks: List[Dict],
    task_index: int,
    strategy: str = "smart_balance",
    weights: Optional[Dict[str, float]] = None,
    current_date: Optional[date] = None
) -> Dict:
    """
    Calculate priority score for a task based on multiple factors.
    
    Args:
        task: Task dictionary with title, due_date, estimated_hours, importance, dependencies
        all_tasks: List of all tasks (for dependency calculation)
        task_index: Index of current task in all_tasks
        strategy: Scoring strategy ("fastest_wins", "high_impact", "deadline_driven", "smart_balance")
        weights: Custom weights dict with keys: urgency, importance, effort, dependencies
        current_date: Current date for urgency calculation (defaults to today)
    
    Returns:
        Dictionary with score, breakdown, and explanation
    """
    if current_date is None:
        current_date = date.today()
    
    # Default weights for smart_balance strategy
    default_weights = {
        "urgency": 0.35,
        "importance": 0.30,
        "effort": 0.20,
        "dependencies": 0.15
    }
    
    # Strategy-specific weights
    strategy_weights = {
        "fastest_wins": {
            "urgency": 0.20,
            "importance": 0.20,
            "effort": 0.50,
            "dependencies": 0.10
        },
        "high_impact": {
            "urgency": 0.20,
            "importance": 0.60,
            "effort": 0.10,
            "dependencies": 0.10
        },
        "deadline_driven": {
            "urgency": 0.70,
            "importance": 0.15,
            "effort": 0.10,
            "dependencies": 0.05
        },
        "smart_balance": default_weights
    }
    
    # Use custom weights if provided, otherwise use strategy weights
    if weights:
        final_weights = weights
    else:
        final_weights = strategy_weights.get(strategy, default_weights)
    
    # Calculate individual component scores
    urgency = calculate_urgency_score(task.get('due_date'), current_date)
    importance = calculate_importance_score(task.get('importance', 5))
    effort = calculate_effort_score(task.get('estimated_hours', 8))
    dependencies = calculate_dependency_score(task, all_tasks, task_index)
    
    # Calculate weighted score
    score = (
        urgency * final_weights["urgency"] +
        importance * final_weights["importance"] +
        effort * final_weights["effort"] +
        dependencies * final_weights["dependencies"]
    )
    
    # Build explanation
    explanation_parts = []
    if urgency > 70:
        explanation_parts.append("urgent deadline")
    if importance > 70:
        explanation_parts.append("high importance")
    if effort > 70:
        explanation_parts.append("quick win (low effort)")
    if dependencies > 50:
        explanation_parts.append("blocks other tasks")
    
    if not explanation_parts:
        explanation_parts.append("moderate priority across factors")
    
    explanation = f"Prioritized due to: {', '.join(explanation_parts)}"
    
    return {
        "score": round(score, 2),
        "breakdown": {
            "urgency": round(urgency, 2),
            "importance": round(importance, 2),
            "effort": round(effort, 2),
            "dependencies": round(dependencies, 2)
        },
        "explanation": explanation
    }


def analyze_and_sort_tasks(
    tasks: List[Dict],
    strategy: str = "smart_balance",
    weights: Optional[Dict[str, float]] = None,
    current_date: Optional[date] = None
) -> List[Dict]:
    """
    Analyze a list of tasks and return them sorted by priority score.
    
    Args:
        tasks: List of task dictionaries
        strategy: Scoring strategy
        weights: Custom weights (optional)
        current_date: Current date for calculations
    
    Returns:
        List of tasks with added 'priority_score' and 'score_breakdown' fields, sorted by score
    """
    if not tasks:
        return []
    
    # Detect circular dependencies
    cycles = detect_circular_dependencies(tasks)
    if cycles:
        # Flag tasks in cycles
        cycle_tasks = set()
        for cycle in cycles:
            cycle_tasks.update(cycle)
        
        for idx in cycle_tasks:
            if idx < len(tasks):
                tasks[idx]['_circular_dependency'] = True
    
    # Calculate scores for all tasks
    scored_tasks = []
    for idx, task in enumerate(tasks):
        # Validate required fields
        if not task.get('title'):
            continue
        
        # Set defaults for missing fields
        task_copy = {
            'id': task.get('id', idx),
            'title': task.get('title', 'Untitled Task'),
            'due_date': task.get('due_date'),
            'estimated_hours': task.get('estimated_hours', 8),
            'importance': task.get('importance', 5),
            'dependencies': task.get('dependencies', [])
        }
        
        # Calculate priority
        priority_data = calculate_priority_score(
            task_copy,
            tasks,
            idx,
            strategy,
            weights,
            current_date
        )
        
        task_copy['priority_score'] = priority_data['score']
        task_copy['score_breakdown'] = priority_data['breakdown']
        task_copy['explanation'] = priority_data['explanation']
        
        if task.get('_circular_dependency'):
            task_copy['_circular_dependency'] = True
            task_copy['explanation'] += " (⚠️ Circular dependency detected)"
        
        scored_tasks.append(task_copy)
    
    # Sort by priority score (descending)
    scored_tasks.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
    
    return scored_tasks

