import unittest
import json
import os
import sqlite3
from datetime import datetime, timedelta

# Import our app and database helpers
# Set environment so db uses a temporary testing path if desired, or just use default.
# For simplicity, we can inspect test tasks.
from app import app
import database.db as db

class AdishiDayplanTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Point to a temporary db for testing
        db.DB_PATH = os.path.join(db.DB_DIR, 'test_planner.db')
        db.init_db()
        
        # Clear out existing tasks from test database
        conn = db.get_db_connection()
        conn.execute("DELETE FROM tasks")
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(db.DB_PATH):
            os.remove(db.DB_PATH)

    def test_quote_endpoint(self):
        """Test getting a motivational quote."""
        response = self.client.get('/api/quote')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('text', data)
        self.assertIn('author', data)

    def test_create_task(self):
        """Test task creation."""
        payload = {
            'title': 'Test Task Title',
            'description': 'Test Description',
            'date': '2026-06-17',
            'priority': 'high'
        }
        response = self.client.post('/api/tasks', 
                                    data=json.dumps(payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIsNotNone(data['id'])
        self.assertEqual(data['title'], 'Test Task Title')
        self.assertEqual(data['description'], 'Test Description')
        self.assertEqual(data['priority'], 'high')
        self.assertEqual(data['completed'], 0)

    def test_get_tasks_filters(self):
        """Test getting tasks and applying filters."""
        # Insert a few mock tasks
        db.create_task('Task 1', 'Desc 1', '2026-06-17', 'high', 0)
        db.create_task('Task 2', 'Desc 2', '2026-06-18', 'low', 1)
        
        # Fetch all
        response = self.client.get('/api/tasks')
        self.assertEqual(response.status_code, 200)
        tasks = json.loads(response.data)
        self.assertEqual(len(tasks), 2)
        
        # Filter by priority
        response = self.client.get('/api/tasks?priority=high')
        tasks = json.loads(response.data)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'Task 1')
        
        # Filter by status (completed = true)
        response = self.client.get('/api/tasks?completed=true')
        tasks = json.loads(response.data)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'Task 2')

    def test_update_task_details_and_completion(self):
        """Test updating a task's fields and toggle completion."""
        task_id = db.create_task('Old Title', 'Old Desc', '2026-06-17', 'medium', 0)
        
        # Update title and complete task
        payload = {
            'title': 'New Title',
            'completed': 1
        }
        response = self.client.put(f'/api/tasks/{task_id}',
                                   data=json.dumps(payload),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        updated_task = json.loads(response.data)
        self.assertEqual(updated_task['title'], 'New Title')
        self.assertEqual(updated_task['completed'], 1)
        # Description should remain unchanged
        self.assertEqual(updated_task['description'], 'Old Desc')

    def test_delete_task(self):
        """Test deleting a task."""
        task_id = db.create_task('To Delete', 'Desc', '2026-06-17', 'low', 0)
        
        response = self.client.delete(f'/api/tasks/{task_id}')
        self.assertEqual(response.status_code, 200)
        
        # Verify it is removed
        task = db.get_task_by_id(task_id)
        self.assertIsNone(task)

    def test_stats_calculations(self):
        """Test calculation of productivity stats."""
        # Setup: 2 high, 1 low. 2 completed, 1 pending
        db.create_task('T1', '', '2026-06-17', 'high', 1)
        db.create_task('T2', '', '2026-06-17', 'high', 0)
        db.create_task('T3', '', '2026-06-18', 'low', 1)
        
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        stats = json.loads(response.data)
        
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['completed'], 2)
        self.assertEqual(stats['pending'], 1)
        # 2 out of 3 = 66.7% completion rate
        self.assertEqual(stats['completion_rate'], 66.7)
        
        # Verify priority breakdown details
        self.assertEqual(stats['priority_breakdown']['high']['total'], 2)
        self.assertEqual(stats['priority_breakdown']['high']['completed'], 1)
        self.assertEqual(stats['priority_breakdown']['low']['total'], 1)
        self.assertEqual(stats['priority_breakdown']['low']['completed'], 1)

if __name__ == '__main__':
    unittest.main()
