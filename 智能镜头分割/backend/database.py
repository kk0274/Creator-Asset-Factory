import sqlite3
import os
import json
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db')

def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            categories TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            product_name TEXT,
            status TEXT DEFAULT 'processing',
            total_scenes INTEGER DEFAULT 0,
            output_dir TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            filename TEXT NOT NULL,
            video_name TEXT,
            creator_name TEXT,
            duration REAL,
            category TEXT,
            correct_category TEXT,
            frame_path TEXT,
            trained BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            category TEXT,
            frame_path TEXT NOT NULL,
            source_task_id INTEGER,
            source_scene_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(source_task_id) REFERENCES tasks(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)

def save_category_set(name, categories):
    conn = get_connection()
    cursor = conn.cursor()
    categories_json = json.dumps(categories, ensure_ascii=False)
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO category_sets (name, categories, updated_at)
            VALUES (?, ?, ?)
        ''', (name, categories_json, datetime.now().isoformat()))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving category set: {e}")
        return False
    finally:
        conn.close()

def get_category_sets():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT name, categories, created_at, updated_at FROM category_sets ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        result = {}
        for row in rows:
            name, categories_json, created_at, updated_at = row
            result[name] = {
                'categories': json.loads(categories_json),
                'created_at': created_at,
                'updated_at': updated_at
            }
        return result
    except Exception as e:
        print(f"Error getting category sets: {e}")
        return {}
    finally:
        conn.close()

def get_category_set(name):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT categories FROM category_sets WHERE name = ?', (name,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None
    except Exception as e:
        print(f"Error getting category set: {e}")
        return None
    finally:
        conn.close()

def delete_category_set(name):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM category_sets WHERE name = ?', (name,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting category set: {e}")
        return False
    finally:
        conn.close()

def rename_category_set(old_name, new_name):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('UPDATE category_sets SET name = ?, updated_at = ? WHERE name = ?', 
                      (new_name, datetime.now().isoformat(), old_name))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error renaming category set: {e}")
        return False
    finally:
        conn.close()

def create_task(name, product_name=None, output_dir=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO tasks (name, product_name, output_dir, created_at)
            VALUES (?, ?, ?, ?)
        ''', (name, product_name, output_dir, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error creating task: {e}")
        return None
    finally:
        conn.close()

def update_task(task_id, status=None, total_scenes=None, completed_at=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if status is not None:
            updates.append('status = ?')
            params.append(status)
        if total_scenes is not None:
            updates.append('total_scenes = ?')
            params.append(total_scenes)
        if completed_at is not None:
            updates.append('completed_at = ?')
            params.append(completed_at)
        
        if updates:
            params.append(task_id)
            cursor.execute(f'UPDATE tasks SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
        return True
    except Exception as e:
        print(f"Error updating task: {e}")
        return False
    finally:
        conn.close()

def get_tasks_db(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, name, product_name, status, total_scenes, output_dir, created_at, completed_at FROM tasks ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'name': row[1],
                'product_name': row[2],
                'status': row[3],
                'total_scenes': row[4],
                'output_dir': row[5],
                'created_at': row[6],
                'completed_at': row[7]
            })
        return result
    except Exception as e:
        print(f"Error getting tasks: {e}")
        return []
    finally:
        conn.close()

def get_task_db(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, name, product_name, status, total_scenes, output_dir, created_at, completed_at FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'product_name': row[2],
                'status': row[3],
                'total_scenes': row[4],
                'output_dir': row[5],
                'created_at': row[6],
                'completed_at': row[7]
            }
        return None
    except Exception as e:
        print(f"Error getting task: {e}")
        return None
    finally:
        conn.close()

def add_scene(task_id, filename, video_name, creator_name, duration, category=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO scenes (task_id, filename, video_name, creator_name, duration, category)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_id, filename, video_name, creator_name, duration, category))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error adding scene: {e}")
        return None
    finally:
        conn.close()

def update_scene(scene_id, category=None, correct_category=None, trained=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if category is not None:
            updates.append('category = ?')
            params.append(category)
        if correct_category is not None:
            updates.append('correct_category = ?')
            params.append(correct_category)
        if trained is not None:
            updates.append('trained = ?')
            params.append(trained)
        
        if updates:
            params.append(scene_id)
            cursor.execute(f'UPDATE scenes SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
        return True
    except Exception as e:
        print(f"Error updating scene: {e}")
        return False
    finally:
        conn.close()

def get_scenes(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, filename, video_name, creator_name, duration, category, correct_category, trained FROM scenes WHERE task_id = ?', (task_id,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'filename': row[1],
                'video_name': row[2],
                'creator_name': row[3],
                'duration': row[4],
                'category': row[5],
                'correct_category': row[6],
                'trained': row[7]
            })
        return result
    except Exception as e:
        print(f"Error getting scenes: {e}")
        return []
    finally:
        conn.close()

def add_training_sample(product_name, category, frame_path, source_task_id=None, source_scene_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO training_samples (product_name, category, frame_path, source_task_id, source_scene_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (product_name, category, frame_path, source_task_id, source_scene_id, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error adding training sample: {e}")
        return None
    finally:
        conn.close()

def get_training_samples_db(product_name=None, category=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        query = 'SELECT id, product_name, category, frame_path, source_task_id, source_scene_id, created_at FROM training_samples WHERE 1=1'
        params = []
        
        if product_name:
            query += ' AND product_name = ?'
            params.append(product_name)
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY created_at DESC'
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'product_name': row[1],
                'category': row[2],
                'frame_path': row[3],
                'source_task_id': row[4],
                'source_scene_id': row[5],
                'created_at': row[6]
            })
        return result
    except Exception as e:
        print(f"Error getting training samples: {e}")
        return []
    finally:
        conn.close()

def get_training_summary(product_name=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        query = 'SELECT category, COUNT(*) as count FROM training_samples WHERE 1=1'
        params = []
        
        if product_name:
            query += ' AND product_name = ?'
            params.append(product_name)
        
        query += ' GROUP BY category ORDER BY count DESC'
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = {}
        total = 0
        for row in rows:
            result[row[0]] = row[1]
            total += row[1]
        return result, total
    except Exception as e:
        print(f"Error getting training summary: {e}")
        return {}, 0
    finally:
        conn.close()

init_db()
