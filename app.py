from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from database.db import (
    init_db, get_all_tasks, get_task_by_id,
    create_task, update_task, delete_task, get_productivity_stats,
    create_user, get_user_by_username, get_user_by_id
)
import random
import os
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Set a secret key for session signing. In production, this should be loaded from env.
app.secret_key = os.environ.get('SECRET_KEY', 'adishi-dayplan-super-secret-development-key-13579')

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

# --- AUTHENTICATION DECORATOR ---

def login_required(f):
    """Decorator to protect routes from unauthenticated users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Check if it is an API route
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- PAGES / VIEW ROUTING ---

@app.route('/')
@login_required
def index():
    """Render the main single page dashboard, injecting the logged in user's details."""
    username = session.get('username')
    return render_template('index.html', username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            error = "Please fill in all fields."
        else:
            user = get_user_by_username(username)
            if user and check_password_hash(user['password_hash'], password):
                # Authentication success - save session
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('index'))
            else:
                error = "Incorrect username or password."
                
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new user registration."""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not password or not confirm_password:
            error = "Please fill in all fields."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            # Check if username already exists
            existing_user = get_user_by_username(username)
            if existing_user:
                error = "Username is already taken."
            else:
                # Hash password and create user
                password_hash = generate_password_hash(password)
                user_id = create_user(username, password_hash)
                if user_id:
                    success = "Registration successful! You can now log in."
                    # Redirect to login page after brief display, or immediately
                    return render_template('login.html', success=success)
                else:
                    error = "Failed to register user. Please try again."
                    
    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    """Clear session data and redirect to login page."""
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# --- TASK REST API ENDPOINTS (SCOPED BY LOGGED IN USER) ---

@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Retrieve tasks belonging to the current user with optional filters."""
    user_id = session['user_id']
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

    tasks = get_all_tasks(user_id, filters)
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
@login_required
def add_task():
    """Create a new task for the current user."""
    user_id = session['user_id']
    data = request.get_json()
    
    if not data or 'title' not in data or not data['title'].strip():
        return jsonify({'error': 'Title is required'}), 400
        
    title = data['title'].strip()
    description = data.get('description', '').strip()
    
    date_str = data.get('date')
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    else:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Expected YYYY-MM-DD.'}), 400
            
    priority = data.get('priority', 'medium').lower()
    if priority not in ['high', 'medium', 'low']:
        priority = 'medium'
        
    completed = 1 if data.get('completed') else 0
    
    new_id = create_task(user_id, title, description, date_str, priority, completed)
    new_task = get_task_by_id(new_id, user_id)
    
    return jsonify(new_task), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def edit_task(task_id):
    """Update a task belonging to the current user."""
    user_id = session['user_id']
    task = get_task_by_id(task_id, user_id)
    if not task:
        return jsonify({'error': 'Task not found or unauthorized'}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Payload required'}), 400
        
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
        
    success = update_task(task_id, user_id, title, description, date_str, priority, completed)
    
    if success:
        updated_task = get_task_by_id(task_id, user_id)
        return jsonify(updated_task)
    else:
        return jsonify({'error': 'Update failed'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def remove_task(task_id):
    """Delete a task belonging to the current user."""
    user_id = session['user_id']
    task = get_task_by_id(task_id, user_id)
    if not task:
        return jsonify({'error': 'Task not found or unauthorized'}), 404
        
    success = delete_task(task_id, user_id)
    if success:
        return jsonify({'message': 'Task deleted successfully'})
    else:
        return jsonify({'error': 'Delete failed'}), 500

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Retrieve productivity statistics for the current user."""
    user_id = session['user_id']
    stats = get_productivity_stats(user_id)
    return jsonify(stats)

@app.route('/api/quote', methods=['GET'])
def get_quote():
    """Get a random motivational quote (public)."""
    quote = random.choice(MOTIVATIONAL_QUOTES)
    return jsonify(quote)

if __name__ == '__main__':
    # Running with debug mode but without watchdog reloader to avoid import errors
    app.run(debug=True, port=5000, use_reloader=False)
