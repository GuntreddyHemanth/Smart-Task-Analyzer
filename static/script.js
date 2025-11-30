// Task Analyzer Frontend JavaScript

let tasks = [];
let taskIdCounter = 0;

// DOM Elements
const taskForm = document.getElementById('taskForm');
const bulkInput = document.getElementById('bulkInput');
const loadBulkBtn = document.getElementById('loadBulk');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const taskList = document.getElementById('taskList');
const taskCount = document.getElementById('taskCount');
const outputSection = document.getElementById('outputSection');
const resultsContainer = document.getElementById('resultsContainer');
const loadingOverlay = document.getElementById('loadingOverlay');
const errorMessage = document.getElementById('errorMessage');
const strategySelect = document.getElementById('strategy');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSampleTasks();
    updateTaskList();
});

// Load sample tasks for demonstration
function loadSampleTasks() {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 7);
    
    tasks = [
        {
            id: taskIdCounter++,
            title: 'Fix critical login bug',
            due_date: tomorrow.toISOString().split('T')[0],
            estimated_hours: 3,
            importance: 9,
            dependencies: []
        },
        {
            id: taskIdCounter++,
            title: 'Update documentation',
            due_date: nextWeek.toISOString().split('T')[0],
            estimated_hours: 2,
            importance: 5,
            dependencies: []
        },
        {
            id: taskIdCounter++,
            title: 'Refactor user authentication',
            due_date: null,
            estimated_hours: 8,
            importance: 7,
            dependencies: [0] // Depends on fixing login bug
        }
    ];
    updateTaskList();
}

// Handle individual task form submission
taskForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const formData = new FormData(taskForm);
    const dependencies = formData.get('dependencies')
        ? formData.get('dependencies').split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
        : [];
    
    const task = {
        id: taskIdCounter++,
        title: formData.get('title'),
        due_date: formData.get('due_date') || null,
        estimated_hours: parseFloat(formData.get('estimated_hours')),
        importance: parseInt(formData.get('importance')),
        dependencies: dependencies
    };
    
    tasks.push(task);
    taskForm.reset();
    updateTaskList();
    showSuccess('Task added successfully!');
});

// Handle bulk JSON input
loadBulkBtn.addEventListener('click', () => {
    try {
        const jsonText = bulkInput.value.trim();
        if (!jsonText) {
            showError('Please enter JSON data');
            return;
        }
        
        const parsedTasks = JSON.parse(jsonText);
        if (!Array.isArray(parsedTasks)) {
            showError('JSON must be an array of tasks');
            return;
        }
        
        // Add IDs to tasks if missing
        parsedTasks.forEach(task => {
            if (!task.id) {
                task.id = taskIdCounter++;
            } else {
                taskIdCounter = Math.max(taskIdCounter, task.id + 1);
            }
        });
        
        tasks = [...tasks, ...parsedTasks];
        bulkInput.value = '';
        updateTaskList();
        showSuccess(`Loaded ${parsedTasks.length} task(s) from JSON`);
    } catch (error) {
        showError('Invalid JSON format: ' + error.message);
    }
});

// Remove task
function removeTask(taskId) {
    tasks = tasks.filter(t => t.id !== taskId);
    updateTaskList();
}

// Update task list display
function updateTaskList() {
    taskCount.textContent = tasks.length;
    analyzeBtn.disabled = tasks.length === 0;
    
    if (tasks.length === 0) {
        taskList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><p>No tasks yet. Add some tasks to get started!</p></div>';
        return;
    }
    
    taskList.innerHTML = tasks.map(task => `
        <div class="task-item">
            <div class="task-item-info">
                <div class="task-item-title">${escapeHtml(task.title)}</div>
                <div class="task-item-details">
                    ${task.due_date ? `Due: ${task.due_date} • ` : ''}
                    ${task.estimated_hours}h • 
                    Importance: ${task.importance}/10
                    ${task.dependencies.length > 0 ? ` • Depends on: ${task.dependencies.join(', ')}` : ''}
                </div>
            </div>
            <button class="task-item-remove" onclick="removeTask(${task.id})">Remove</button>
        </div>
    `).join('');
}

// Analyze tasks
analyzeBtn.addEventListener('click', async () => {
    if (tasks.length === 0) {
        showError('Please add at least one task');
        return;
    }
    
    loadingOverlay.style.display = 'flex';
    errorMessage.style.display = 'none';
    
    try {
        const strategy = strategySelect.value;
        const response = await fetch('/api/tasks/analyze/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks,
                strategy: strategy
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to analyze tasks');
        }
        
        const data = await response.json();
        displayResults(data);
        showSuccess('Tasks analyzed successfully!');
    } catch (error) {
        showError('Error analyzing tasks: ' + error.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

// Display analysis results
function displayResults(data) {
    outputSection.style.display = 'block';
    
    const warnings = data.warnings || [];
    const strategyName = {
        'smart_balance': 'Smart Balance',
        'fastest_wins': 'Fastest Wins',
        'high_impact': 'High Impact',
        'deadline_driven': 'Deadline Driven'
    }[data.strategy_used] || data.strategy_used;
    
    let html = `
        <div style="margin-bottom: 20px;">
            <p><strong>Strategy:</strong> ${strategyName}</p>
            <p><strong>Total Tasks:</strong> ${data.total_tasks}</p>
        </div>
    `;
    
    if (warnings.length > 0) {
        html += warnings.map(w => `<div class="warning">⚠️ ${escapeHtml(w)}</div>`).join('');
    }
    
    data.tasks.forEach((task, index) => {
        const priority = getPriorityLevel(task.priority_score);
        const breakdown = task.score_breakdown || {};
        
        html += `
            <div class="result-item ${priority.class}">
                <div class="result-header">
                    <div class="result-title">#${index + 1}: ${escapeHtml(task.title)}</div>
                    <span class="priority-badge ${priority.class}">${priority.label}</span>
                </div>
                
                <div class="score-display">Score: ${task.priority_score.toFixed(2)}</div>
                
                <div class="score-breakdown">
                    <div class="score-item">
                        <div class="score-item-label">Urgency</div>
                        <div class="score-item-value">${breakdown.urgency || 0}</div>
                    </div>
                    <div class="score-item">
                        <div class="score-item-label">Importance</div>
                        <div class="score-item-value">${breakdown.importance || 0}</div>
                    </div>
                    <div class="score-item">
                        <div class="score-item-label">Effort</div>
                        <div class="score-item-value">${breakdown.effort || 0}</div>
                    </div>
                    <div class="score-item">
                        <div class="score-item-label">Dependencies</div>
                        <div class="score-item-value">${breakdown.dependencies || 0}</div>
                    </div>
                </div>
                
                <div class="explanation">
                    💡 ${escapeHtml(task.explanation || 'No explanation available')}
                </div>
                
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666;">
                    <strong>Details:</strong><br>
                    ${task.due_date ? `Due: ${task.due_date} • ` : 'No due date • '}
                    ${task.estimated_hours}h estimated • 
                    Importance: ${task.importance}/10
                    ${task.dependencies && task.dependencies.length > 0 ? ` • Dependencies: ${task.dependencies.join(', ')}` : ''}
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
    
    // Scroll to results
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Get priority level from score
function getPriorityLevel(score) {
    if (score >= 70) {
        return { class: 'high-priority', label: 'High' };
    } else if (score >= 40) {
        return { class: 'medium-priority', label: 'Medium' };
    } else {
        return { class: 'low-priority', label: 'Low' };
    }
}

// Clear all tasks
clearBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear all tasks?')) {
        tasks = [];
        taskIdCounter = 0;
        updateTaskList();
        outputSection.style.display = 'none';
        showSuccess('All tasks cleared');
    }
});

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    // Simple success notification (could be enhanced)
    console.log('Success:', message);
}

// Make removeTask available globally
window.removeTask = removeTask;

