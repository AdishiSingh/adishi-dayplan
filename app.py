from flask import Flask, jsonify, request, render_template
from database.db import (
    init_db, get_all_tasks, get_task_by_id,
    create_task, update_task, delete_task, get_productivity_stats
)
import random
from datetime import datetime

app = Flask(__name__)

# Initialize database
init_db()

# List of motivational productivity quotes
MOTIVATIONAL_QUOTES = [
    {"text": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
    {"text": "Focus on being productive instead of busy.", "author": "Tim Ferriss"},
    {"text": "Your mind is for having ideas, not holding them.", "author": "David Allen"},
    {"text": "You do not rise to the level of your goals. You fall to the level of your systems.", "author": "James Clear"},
    {"text": "The best way to predict the future is to create it.", "author": "Peter Drucker"},
    {"text": "Action is the foundational key to all success.", "author": "Pablo Picasso"},
    {"text": "Done is better than perfect.", "author": "Sheryl Sandberg"},
    {"text": "Make each day your masterpiece.", "author": "John Wooden"},
    {"text": "Tomorrow is often the busiest day of the week.", "author": "Spanish Proverb"},
    {"text": "It is not enough to be busy. So are the ants. The question is: What are we busy about?", "author": "Henry David Thoreau"},
    {"text": "Don't count the days, make the days count.", "author": "Muhammad Ali"},
    {"text": "Concentrate all your thoughts upon the work at hand. The sun's rays do not burn until brought to a focus.", "author": "Alexander Graham Bell"}
]

@app.route('/')
def index():
    """Render the main single page dashboard."""
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Retrieve tasks with optional filters from query parameters."""
    filters = {}
    
    # Extract filters
    date_filter = request.args.get('date')
    if date_filter:
        filters['date'] = date_filter
        
    priority_filter = request.args.get('priority')
    if priority_filter:
        filters['priority'] = priority_filter
        
    completed_filter = request.args.get('completed')
    if completed_filter is not None:
        if completed_filter.lower() == 'true':
            filters['completed'] = 1
        elif completed_filter.lower() == 'false':
            filters['completed'] = 0
            
    search_filter = request.args.get('search')
    if search_filter:
        filters['search'] = search_filter

    tasks = get_all_tasks(filters)
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Create a new task."""
    data = request.get_json()
    
    if not data or 'title' not in data or not data['title'].strip():
        return jsonify({'error': 'Title is required'}), 400
        
    title = data['title'].strip()
    description = data.get('description', '').strip()
    
    # Default date is today if not provided (YYYY-MM-DD)
    date_str = data.get('date')
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    else:
        try:
            # Validate date format
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Expected YYYY-MM-DD.'}), 400
            
    priority = data.get('priority', 'medium').lower()
    if priority not in ['high', 'medium', 'low']:
        priority = 'medium'
        
    completed = 1 if data.get('completed') else 0
    
    new_id = create_task(title, description, date_str, priority, completed)
    new_task = get_task_by_id(new_id)
    
    return jsonify(new_task), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def edit_task(task_id):
    """Update an existing task's details or completion status."""
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Payload required'}), 400
        
    # Keep old values if not provided in request
    title = data.get('title', task['title']).strip()
    if not title:
        return jsonify({'error': 'Title cannot be empty'}), 400
        
    description = data.get('description', task['description']).strip()
    
    date_str = data.get('date', task['date'])
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Expected YYYY-MM-DD.'}), 400
        
    priority = data.get('priority', task['priority']).lower()
    if priority not in ['high', 'medium', 'low']:
        priority = task['priority']
        
    completed = int(data.get('completed', task['completed']))
    if completed not in [0, 1]:
        completed = task['completed']
        
    success = update_task(task_id, title, description, date_str, priority, completed)
    
    if success:
        updated_task = get_task_by_id(task_id)
        return jsonify(updated_task)
    else:
        return jsonify({'error': 'Update failed'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def remove_task(task_id):
    """Delete a task."""
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
        
    success = delete_task(task_id)
    if success:
        return jsonify({'message': 'Task deleted successfully'})
    else:
        return jsonify({'error': 'Delete failed'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retrieve productivity statistics."""
    stats = get_productivity_stats()
    return jsonify(stats)

@app.route('/api/quote', methods=['GET'])
def get_quote():
    """Get a random motivational quote."""
    quote = random.choice(MOTIVATIONAL_QUOTES)
    return jsonify(quote)

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
