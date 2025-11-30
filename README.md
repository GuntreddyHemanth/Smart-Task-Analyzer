# Smart Task Analyzer

A Django-based task management system that intelligently scores and prioritizes tasks based on multiple factors including urgency, importance, effort, and dependencies.

## Overview

The Smart Task Analyzer helps users identify which tasks they should work on first by calculating priority scores using a sophisticated algorithm that balances multiple factors. The system supports multiple sorting strategies and provides detailed explanations for why each task received its score.

## Features

- **Intelligent Priority Scoring**: Calculates task priority based on:
  - **Urgency**: How soon is the task due? (Past-due tasks get exponential penalties)
  - **Importance**: User-provided rating (1-10 scale)
  - **Effort**: Lower effort tasks are prioritized as "quick wins"
  - **Dependencies**: Tasks that block other tasks rank higher

- **Multiple Sorting Strategies**:
  - **Smart Balance**: Balances all factors (recommended)
  - **Fastest Wins**: Prioritizes low-effort tasks
  - **High Impact**: Prioritizes importance over everything
  - **Deadline Driven**: Prioritizes based on due date

- **Circular Dependency Detection**: Automatically detects and flags circular dependencies

- **Modern Web Interface**: Clean, responsive UI with:
  - Individual task input form
  - Bulk JSON import
  - Visual priority indicators (High/Medium/Low)
  - Detailed score breakdowns
  - Explanations for each task's priority

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Smart-Task-Analyzer
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the application**:
   - Open your browser and navigate to `http://127.0.0.1:8000/`
   - The main interface will load with sample tasks

## Algorithm Explanation

The priority scoring algorithm uses a weighted combination of four key factors:

### 1. Urgency Score (0-100)
- **Past due dates**: Exponential penalty starting at 50, increasing by 5 points per day overdue (capped at 100)
- **Due today**: 90 points
- **Due tomorrow**: 80 points
- **Due in 2-3 days**: 70 points
- **Due in a week**: 50 points
- **Due in 2 weeks**: 30 points
- **Due in a month**: 15 points
- **Far future**: Logarithmic decay to minimum of 5 points

### 2. Importance Score (0-100)
- Direct linear mapping from user's 1-10 importance rating
- Formula: `(importance / 10) * 100`
- Ensures values are clamped between 1-10

### 3. Effort Score (0-100)
- Inverse relationship: lower effort = higher score (quick wins)
- **≤1 hour**: 100 points
- **≤2 hours**: 90 points
- **≤4 hours**: 75 points
- **≤8 hours**: 60 points
- **≤16 hours**: 40 points
- **>16 hours**: Logarithmic decay to minimum of 10 points

### 4. Dependency Score (0-100)
- Tasks that block other tasks get higher scores
- Formula: `min(100, blocking_count * 20)`
- Each blocked task adds 20 points (capped at 100)

### Weighted Combination

The final priority score is calculated as:
```
score = (urgency × w_urgency) + (importance × w_importance) + 
        (effort × w_effort) + (dependencies × w_dependencies)
```

**Default weights (Smart Balance)**:
- Urgency: 35%
- Importance: 30%
- Effort: 20%
- Dependencies: 15%

**Strategy-specific weights**:
- **Fastest Wins**: Effort 50%, others balanced
- **High Impact**: Importance 60%, others reduced
- **Deadline Driven**: Urgency 70%, others minimal

### Edge Cases Handled

1. **Past Due Dates**: Exponential penalty ensures overdue tasks are prioritized
2. **Missing Data**: Defaults provided (importance=5, estimated_hours=8, no due_date=0 urgency)
3. **Circular Dependencies**: Detected using DFS algorithm, flagged with warnings
4. **Invalid Inputs**: Comprehensive validation with clear error messages
5. **Zero/Invalid Values**: Clamped to valid ranges or set to safe defaults

## Design Decisions

### 1. Algorithm Design
- **Why weighted combination?**: Allows flexibility while maintaining interpretability. Different strategies can be implemented by adjusting weights.
- **Why exponential penalty for overdue?**: Prevents tasks from being ignored indefinitely. The penalty grows to ensure overdue tasks eventually become top priority.
- **Why inverse effort scoring?**: Encourages "quick wins" which can boost productivity and morale, while still considering other factors.

### 2. Circular Dependency Detection
- **DFS-based approach**: Efficient and can detect all cycles in a single pass
- **Warning system**: Rather than blocking, we flag cycles so users can make informed decisions
- **Why not prevent cycles?**: Sometimes legitimate circular dependencies exist (e.g., iterative development), so we inform rather than restrict

### 3. API Design
- **RESTful endpoints**: Clear separation between analysis and suggestions
- **Flexible input**: Accepts both individual tasks and bulk JSON
- **Custom weights**: Allows power users to fine-tune the algorithm
- **Error handling**: Comprehensive validation with descriptive error messages

### 4. Frontend Design
- **Progressive enhancement**: Works without JavaScript for basic functionality
- **Responsive design**: Mobile-friendly grid layout that adapts to screen size
- **Visual feedback**: Color-coded priorities, loading states, error messages
- **User experience**: Sample tasks on load, clear instructions, intuitive interface

### 5. Testing Strategy
- **Unit tests for core algorithm**: Tests each scoring component independently
- **Integration tests**: Tests full analyze_and_sort_tasks function
- **Edge case coverage**: Tests for missing data, invalid inputs, circular dependencies
- **Strategy validation**: Ensures different strategies produce expected results

## Time Breakdown

- **Backend Development**: ~2.5 hours
  - Algorithm design and implementation: 1 hour
  - API endpoints and validation: 45 minutes
  - Models and serializers: 30 minutes
  - Testing: 15 minutes

- **Frontend Development**: ~1.5 hours
  - HTML structure and forms: 30 minutes
  - CSS styling and responsive design: 45 minutes
  - JavaScript functionality: 30 minutes
  - Integration and testing: 15 minutes

- **Documentation**: ~30 minutes
  - README: 20 minutes
  - Code comments: 10 minutes

**Total**: Approximately 4.5 hours

## API Endpoints

### POST `/api/tasks/analyze/`

Analyze and sort tasks by priority.

**Request Body**:
```json
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
  "strategy": "smart_balance",
  "weights": {
    "urgency": 0.4,
    "importance": 0.3,
    "effort": 0.2,
    "dependencies": 0.1
  }
}
```

**Response**:
```json
{
  "tasks": [
    {
      "id": 0,
      "title": "Fix login bug",
      "priority_score": 75.5,
      "score_breakdown": {
        "urgency": 80.0,
        "importance": 80.0,
        "effort": 75.0,
        "dependencies": 0.0
      },
      "explanation": "Prioritized due to: urgent deadline, high importance, quick win (low effort)"
    }
  ],
  "strategy_used": "smart_balance",
  "total_tasks": 1,
  "warnings": []
}
```

### GET `/api/tasks/suggest/`

Get suggestions for top tasks (returns instructions for using analyze endpoint).

**Query Parameters**:
- `strategy`: Optional, sorting strategy (default: "smart_balance")
- `limit`: Optional, number of suggestions (default: 3)

## Running Tests

```bash
python manage.py test tasks.tests
```

The test suite includes:
- Urgency score calculations
- Importance score calculations
- Effort score calculations
- Dependency score calculations
- Priority score calculations for all strategies
- Circular dependency detection
- Full analyze and sort functionality
- Edge case handling

## Project Structure

```
Smart-Task-Analyzer/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
├── smartanalyzer/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── tasks/
│   ├── __init__.py
│   ├── models.py          # Task model
│   ├── views.py           # API endpoints
│   ├── urls.py            # URL routing
│   ├── serializers.py     # Data validation
│   ├── scoring.py         # Priority algorithm
│   ├── tests.py           # Unit tests
│   └── admin.py
├── templates/
│   └── tasks/
│       └── index.html      # Frontend HTML
└── static/
    ├── styles.css         # Frontend CSS
    └── script.js          # Frontend JavaScript
```

## Future Improvements

Given more time, I would implement:

1. **Database Persistence**: Store tasks in database for persistence across sessions
2. **User Authentication**: Multi-user support with personal task lists
3. **Dependency Graph Visualization**: Visual representation of task dependencies
4. **Date Intelligence**: Consider weekends and holidays in urgency calculations
5. **Eisenhower Matrix View**: 2D grid visualization (Urgent vs Important)
6. **Learning System**: User feedback to improve algorithm weights
7. **Task Templates**: Pre-defined task templates for common workflows
8. **Export/Import**: Export tasks to CSV, JSON, or other formats
9. **Task History**: Track completed tasks and analyze productivity patterns
10. **Notifications**: Reminders for upcoming deadlines
11. **Collaboration**: Share task lists with team members
12. **Advanced Analytics**: Charts and graphs showing task distribution and trends

## Bonus Challenges (Not Implemented)

The following bonus features were not implemented due to time constraints, but would be valuable additions:

- **Dependency Graph Visualization**: Would use a library like D3.js or vis.js to create interactive dependency graphs
- **Date Intelligence**: Would integrate with a calendar API to exclude weekends/holidays
- **Eisenhower Matrix**: Would create a 2D scatter plot with urgency vs importance axes
- **Learning System**: Would store user feedback and use machine learning to adjust weights

## Troubleshooting

### Common Issues

1. **Static files not loading**:
   - Run `python manage.py collectstatic` (if in production)
   - Ensure `STATIC_URL` and `STATICFILES_DIRS` are configured in settings.py

2. **CSRF errors**:
   - The API endpoints use `@csrf_exempt` for simplicity. In production, implement proper CSRF protection.

3. **Database errors**:
   - Run migrations: `python manage.py migrate`
   - Delete `db.sqlite3` and re-run migrations if needed

4. **Import errors**:
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

## License

This project is created as an assignment submission. All rights reserved.

## Author

Created as part of a technical assessment for task management system development.

---

**Note**: This application is designed for local development and demonstration purposes. For production deployment, additional considerations such as security, performance optimization, and deployment configuration would be necessary.

