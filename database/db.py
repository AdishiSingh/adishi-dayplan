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
    """Initialize the database tables if they do not exist, migration friendly."""
    # Ensure database directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we need to migrate existing database (i.e. tasks exists but users does not)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    users_table_exists = cursor.fetchone()
    
    if not users_table_exists:
        # To avoid sqlite schema conflicts, drop old tasks table if it has no user_id column
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        tasks_table_exists = cursor.fetchone()
        
        if tasks_table_exists:
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [row['name'] for row in cursor.fetchall()]
            if 'user_id' not in columns:
                # Drop old tasks table without user association
                cursor.execute("DROP TABLE tasks")
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create tasks table (with foreign key linking to users)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,          -- Format: YYYY-MM-DD
            priority TEXT NOT NULL,      -- high, medium, low
            completed INTEGER DEFAULT 0, -- 0 = incomplete, 1 = completed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# --- USER MANAGEMENT CRUD ---

def create_user(username, password_hash):
    """Register a new user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        ''', (username, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None # Username already exists

def get_user_by_username(username):
    """Retrieve user details by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    """Retrieve user details by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# --- TASK MANAGEMENT CRUD (SCOPED BY USER) ---

def get_all_tasks(user_id, filters=None):
    """Retrieve tasks belonging to a specific user with optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tasks WHERE user_id = ?"
    params = [user_id]
    
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

def get_task_by_id(task_id, user_id):
    """Retrieve a single task belonging to a specific user by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_task(user_id, title, description, date, priority, completed=0):
    """Create a new task for a specific user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (user_id, title, description, date, priority, completed)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, title, description, date, priority, completed))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_task(task_id, user_id, title, description, date, priority, completed):
    """Update an existing task belonging to a specific user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks
        SET title = ?, description = ?, date = ?, priority = ?, completed = ?
        WHERE id = ? AND user_id = ?
    ''', (title, description, date, priority, completed, task_id, user_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def delete_task(task_id, user_id):
    """Delete a task belonging to a specific user from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_productivity_stats(user_id):
    """Calculate and return task statistics for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total stats for user
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
    total_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1 AND user_id = ?", (user_id,))
    completed_tasks = cursor.fetchone()[0]
    
    pending_tasks = total_tasks - completed_tasks
    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0
    
    # Stats breakdown by priority
    cursor.execute('''
        SELECT priority, COUNT(*) as count, SUM(completed) as completed 
        FROM tasks 
        WHERE user_id = ? 
        GROUP BY priority
    ''', (user_id,))
    
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
