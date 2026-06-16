import sqlite3
import os

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'planner.db')

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables if they do not exist."""
    # Ensure database directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,          -- Format: YYYY-MM-DD
            priority TEXT NOT NULL,      -- high, medium, low
            completed INTEGER DEFAULT 0, -- 0 = incomplete, 1 = completed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_all_tasks(filters=None):
    """Retrieve tasks with optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    
    if filters:
        if 'date' in filters and filters['date']:
            query += " AND date = ?"
            params.append(filters['date'])
        if 'priority' in filters and filters['priority']:
            query += " AND priority = ?"
            params.append(filters['priority'])
        if 'completed' in filters is not None:
            query += " AND completed = ?"
            params.append(filters['completed'])
        if 'search' in filters and filters['search']:
            query += " AND (title LIKE ? OR description LIKE ?)"
            search_param = f"%{filters['search']}%"
            params.append(search_param)
            params.append(search_param)
            
    query += " ORDER BY date ASC, CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END ASC, created_at DESC"
    
    cursor.execute(query, params)
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def get_task_by_id(task_id):
    """Retrieve a single task by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_task(title, description, date, priority, completed=0):
    """Create a new task in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (title, description, date, priority, completed)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, date, priority, completed))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_task(task_id, title, description, date, priority, completed):
    """Update an existing task in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks
        SET title = ?, description = ?, date = ?, priority = ?, completed = ?
        WHERE id = ?
    ''', (title, description, date, priority, completed, task_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def delete_task(task_id):
    """Delete a task from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_productivity_stats():
    """Calculate and return tasks statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total stats
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1")
    completed_tasks = cursor.fetchone()[0]
    
    pending_tasks = total_tasks - completed_tasks
    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0
    
    # Stats breakdown by priority
    cursor.execute("SELECT priority, COUNT(*) as count, SUM(completed) as completed FROM tasks GROUP BY priority")
    priority_stats = {}
    for row in cursor.fetchall():
        p = row['priority']
        p_total = row['count']
        p_comp = row['completed'] or 0
        priority_stats[p] = {
            'total': p_total,
            'completed': p_comp,
            'pending': p_total - p_comp
        }
        
    for p in ['high', 'medium', 'low']:
        if p not in priority_stats:
            priority_stats[p] = {'total': 0, 'completed': 0, 'pending': 0}
            
    conn.close()
    
    return {
        'total': total_tasks,
        'completed': completed_tasks,
        'pending': pending_tasks,
        'completion_rate': completion_rate,
        'priority_breakdown': priority_stats
    }
