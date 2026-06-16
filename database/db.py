import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

# Normalize and detect database connection string
DB_URL = os.environ.get('DATABASE_URL')
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = DB_URL is not None and DB_URL.startswith("postgresql://")

# Define file paths for SQLite fallback
DB_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(DB_DIR, 'planner.db')

def get_db_connection():
    """Establish a connection to the correct database engine (PostgreSQL or SQLite)."""
    if IS_POSTGRES:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def p(sql_query):
    """Translate standard SQL placeholders (?) to PostgreSQL format (%s) if needed."""
    if IS_POSTGRES:
        return sql_query.replace('?', '%s')
    return sql_query

def get_row_dict(row):
    """Helper to convert database row objects into dictionaries."""
    if row is None:
        return None
    return dict(row)

def init_db():
    """Initialize the database schema for the active engine."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if IS_POSTGRES:
        # PostgreSQL Schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title VARCHAR(150) NOT NULL,
                description TEXT,
                date VARCHAR(10) NOT NULL,          -- Format: YYYY-MM-DD
                priority VARCHAR(10) NOT NULL,      -- high, medium, low
                completed INTEGER DEFAULT 0,        -- 0 = incomplete, 1 = completed
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
    else:
        # SQLite Schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                priority TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
    
    conn.commit()
    conn.close()

def insert_and_get_id(conn, cursor, sql, params):
    """Execute an insert query and fetch the primary key ID depending on the engine."""
    if IS_POSTGRES:
        sql_with_returning = sql + " RETURNING id"
        cursor.execute(p(sql_with_returning), params)
        result = cursor.fetchone()
        return result['id']
    else:
        cursor.execute(p(sql), params)
        return cursor.lastrowid

# --- USER MANAGEMENT CRUD ---

def create_user(username, password_hash):
    """Register a new user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        user_id = insert_and_get_id(conn, cursor, sql, (username, password_hash))
        conn.commit()
        conn.close()
        return user_id
    except (sqlite3.IntegrityError, psycopg2.IntegrityError):
        conn.rollback()
        conn.close()
        return None

def get_user_by_username(username):
    """Retrieve user details by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM users WHERE username = ?"
    cursor.execute(p(sql), (username,))
    row = cursor.fetchone()
    conn.close()
    return get_row_dict(row)

def get_user_by_id(user_id):
    """Retrieve user details by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM users WHERE id = ?"
    cursor.execute(p(sql), (user_id,))
    row = cursor.fetchone()
    conn.close()
    return get_row_dict(row)


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
            like_op = "ILIKE" if IS_POSTGRES else "LIKE"
            query += f" AND (title {like_op} ? OR description {like_op} ?)"
            search_param = f"%{filters['search']}%"
            params.append(search_param)
            params.append(search_param)
            
    query += " ORDER BY date ASC, CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END ASC, created_at DESC"
    
    cursor.execute(p(query), params)
    tasks = [get_row_dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def get_task_by_id(task_id, user_id):
    """Retrieve a single task belonging to a specific user by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM tasks WHERE id = ? AND user_id = ?"
    cursor.execute(p(sql), (task_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return get_row_dict(row)

def create_task(user_id, title, description, date, priority, completed=0):
    """Create a new task for a specific user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO tasks (user_id, title, description, date, priority, completed) VALUES (?, ?, ?, ?, ?, ?)"
    task_id = insert_and_get_id(conn, cursor, sql, (user_id, title, description, date, priority, completed))
    conn.commit()
    conn.close()
    return task_id

def update_task(task_id, user_id, title, description, date, priority, completed):
    """Update an existing task belonging to a specific user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = '''
        UPDATE tasks
        SET title = ?, description = ?, date = ?, priority = ?, completed = ?
        WHERE id = ? AND user_id = ?
    '''
    cursor.execute(p(sql), (title, description, date, priority, completed, task_id, user_id))
    conn.commit()
    
    # Handle count differences (psycopg2 cursor has rowcount, sqlite3 cursor has rowcount)
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def delete_task(task_id, user_id):
    """Delete a task belonging to a specific user from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM tasks WHERE id = ? AND user_id = ?"
    cursor.execute(p(sql), (task_id, user_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_completion_streak(user_id):
    """Calculate the consecutive days of completed tasks ending today or yesterday."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total and completed tasks grouped by date, ordering descending
    sql = '''
        SELECT date, COUNT(*) as total, SUM(completed) as completed
        FROM tasks
        WHERE user_id = ?
        GROUP BY date
        ORDER BY date DESC
    '''
    cursor.execute(p(sql), (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return 0
        
    from datetime import datetime, timedelta
    today = datetime.now().date()
    
    dates_status = {}
    for row in rows:
        p_row = get_row_dict(row)
        d_str = p_row['date']
        try:
            d_obj = datetime.strptime(d_str, '%Y-%m-%d').date()
            dates_status[d_obj] = (int(p_row['total']) == int(p_row['completed']) and int(p_row['total']) > 0)
        except ValueError:
            continue
            
    check_date = today
    # If today has no tasks, start checking from yesterday
    if check_date not in dates_status:
        check_date = today - timedelta(days=1)
        
    streak = 0
    while True:
        if check_date in dates_status:
            if dates_status[check_date]:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        else:
            break
            
    return streak

def get_productivity_stats(user_id):
    """Calculate and return task statistics for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total stats for user
    sql_total = "SELECT COUNT(*) FROM tasks WHERE user_id = ?"
    cursor.execute(p(sql_total), (user_id,))
    total_tasks = cursor.fetchone()[0]
    
    sql_completed = "SELECT COUNT(*) FROM tasks WHERE completed = 1 AND user_id = ?"
    cursor.execute(p(sql_completed), (user_id,))
    completed_tasks = cursor.fetchone()[0]
    
    pending_tasks = total_tasks - completed_tasks
    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0
    
    # Stats breakdown by priority
    sql_priority = '''
        SELECT priority, COUNT(*) as count, SUM(completed) as completed 
        FROM tasks 
        WHERE user_id = ? 
        GROUP BY priority
    '''
    cursor.execute(p(sql_priority), (user_id,))
    
    priority_stats = {}
    for row in cursor.fetchall():
        p_row = get_row_dict(row)
        p_name = p_row['priority']
        p_total = p_row['count']
        p_comp = p_row['completed'] or 0
        priority_stats[p_name] = {
            'total': p_total,
            'completed': int(p_comp),
            'pending': p_total - int(p_comp)
        }
        
    for p_name in ['high', 'medium', 'low']:
        if p_name not in priority_stats:
            priority_stats[p_name] = {'total': 0, 'completed': 0, 'pending': 0}
            
    conn.close()
    
    return {
        'total': total_tasks,
        'completed': completed_tasks,
        'pending': pending_tasks,
        'completion_rate': completion_rate,
        'priority_breakdown': priority_stats,
        'streak': get_completion_streak(user_id)
    }
