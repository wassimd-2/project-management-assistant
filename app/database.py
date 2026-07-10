import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

# Dynamically resolve the path to the storage directory
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "storage" / "project_manager.db"

def get_connection() -> sqlite3.Connection:
    """Creates and returns a database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Returns rows as dictionaries
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _run_query(query: str, parameters: tuple = ()) -> int:
    """Executes an INSERT, UPDATE, or DELETE query and returns the last row ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        conn.commit()
        return cursor.lastrowid

def _fetch_query(query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
    """Executes a SELECT query and returns a list of dictionaries."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        return [dict(row) for row in cursor.fetchall()]

def init_db():
    """Initializes the database schema."""
    # Ensure the storage directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    schema = """
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'Planning',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'To Do',
        assignee TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS dependencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        depends_on_task_id INTEGER NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
        FOREIGN KEY (depends_on_task_id) REFERENCES tasks (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        severity TEXT DEFAULT 'Low',
        status TEXT DEFAULT 'Open',
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intent TEXT,
        tool_used TEXT NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with get_connection() as conn:
        conn.executescript(schema)

# ==========================================
# DYNAMIC UPDATE HELPER
# ==========================================
def _update_record(table: str, record_id: int, **kwargs) -> bool:
    """Dynamically updates a record based on provided kwargs."""
    if not kwargs:
        return False
    
    columns = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values()) + [record_id]
    
    query = f"UPDATE {table} SET {columns} WHERE id = ?"
    _run_query(query, tuple(values))
    return True

# ==========================================
# PROJECTS CRUD
# ==========================================
def create_project(name: str, description: str = "", status: str = "Planning") -> int:
    query = "INSERT INTO projects (name, description, status) VALUES (?, ?, ?)"
    return _run_query(query, (name, description, status))

def get_project(project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    if project_id:
        return _fetch_query("SELECT * FROM projects WHERE id = ?", (project_id,))
    return _fetch_query("SELECT * FROM projects")

def update_project(project_id: int, **kwargs) -> bool:
    return _update_record("projects", project_id, **kwargs)

def delete_project(project_id: int):
    _run_query("DELETE FROM projects WHERE id = ?", (project_id,))

# ==========================================
# TASKS CRUD
# ==========================================
def create_task(project_id: int, name: str, description: str = "", priority: str = "Medium", status: str = "To Do", assignee: str = "") -> int:
    query = "INSERT INTO tasks (project_id, name, description, priority, status, assignee) VALUES (?, ?, ?, ?, ?, ?)"
    return _run_query(query, (project_id, name, description, priority, status, assignee))

def get_tasks(task_id: Optional[int] = None, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    if task_id:
        return _fetch_query("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if project_id:
        return _fetch_query("SELECT * FROM tasks WHERE project_id = ?", (project_id,))
    return _fetch_query("SELECT * FROM tasks")

def update_task(task_id: int, **kwargs) -> bool:
    return _update_record("tasks", task_id, **kwargs)

def delete_task(task_id: int):
    _run_query("DELETE FROM tasks WHERE id = ?", (task_id,))

# ==========================================
# DEPENDENCIES CRUD
# ==========================================
def add_dependency(task_id: int, depends_on_task_id: int) -> int:
    query = "INSERT INTO dependencies (task_id, depends_on_task_id) VALUES (?, ?)"
    return _run_query(query, (task_id, depends_on_task_id))

def get_dependencies(task_id: int) -> List[Dict[str, Any]]:
    # Gets all tasks that the given task_id depends on
    query = """
        SELECT t.* FROM tasks t
        JOIN dependencies d ON t.id = d.depends_on_task_id
        WHERE d.task_id = ?
    """
    return _fetch_query(query, (task_id,))

def remove_dependency(dependency_id: int):
    _run_query("DELETE FROM dependencies WHERE id = ?", (dependency_id,))

# ==========================================
# RISKS CRUD
# ==========================================
def add_risk(project_id: int, description: str, severity: str = "Low", status: str = "Open") -> int:
    query = "INSERT INTO risks (project_id, description, severity, status) VALUES (?, ?, ?, ?)"
    return _run_query(query, (project_id, description, severity, status))

def get_risks(project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    if project_id:
        return _fetch_query("SELECT * FROM risks WHERE project_id = ?", (project_id,))
    return _fetch_query("SELECT * FROM risks")

def update_risk(risk_id: int, **kwargs) -> bool:
    return _update_record("risks", risk_id, **kwargs)

def delete_risk(risk_id: int):
    _run_query("DELETE FROM risks WHERE id = ?", (risk_id,))

# ==========================================
# LOGS CRUD
# ==========================================
def add_log(intent: str, tool_used: str, details: str) -> int:
    query = "INSERT INTO logs (intent, tool_used, details) VALUES (?, ?, ?)"
    return _run_query(query, (intent, tool_used, details))

def get_logs(limit: int = 50) -> List[Dict[str, Any]]:
    return _fetch_query("SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,))

# Initialize the database when the module is imported
init_db()