from typing import Optional
from langchain_core.tools import tool
from app.database import (
    create_project, update_project, delete_project,
    create_task, update_task, delete_task,
    add_dependency, remove_dependency,
    add_risk, update_risk, delete_risk
)
from app.logger import log_agent_action

# ==========================================
# PROJECT ACTIONS
# ==========================================
@tool
def add_new_project(name: str, description: str = "", status: str = "Planning") -> str:
    """Action Tool: Creates a new project profile."""
    p_id = create_project(name, description, status)
    log_agent_action("state_change_create", "add_new_project", f"Created Proj ID {p_id}: {name}")
    return f"Successfully created project '{name}' with ID: {p_id}."

@tool
def modify_project_details(project_id: int, name: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None) -> str:
    """Action Tool: Modifies attributes of an existing project profile."""
    # Filter out None fields so we only pass the updates the model intended
    updates = {k: v for k, v in {"name": name, "description": description, "status": status}.items() if v is not None}
    if not updates:
        return "No modification arguments were provided."
    
    success = update_project(project_id, **updates)
    log_agent_action("state_change_update", "modify_project_details", f"Updated Proj {project_id} fields: {list(updates.keys())}")
    return f"Project {project_id} successfully updated." if success else f"Failed to update Project {project_id}."

@tool
def remove_project(project_id: int) -> str:
    """Action Tool: Deletes a project and cascades deletion to all its tasks/risks."""
    delete_project(project_id)
    log_agent_action("state_change_delete", "remove_project", f"Deleted Project ID: {project_id}")
    return f"Successfully deleted project {project_id} and all related entities."

# ==========================================
# TASK ACTIONS
# ==========================================
@tool
def add_project_task(project_id: int, name: str, description: str = "", priority: str = "Medium", status: str = "To Do", assignee: str = "") -> str:
    """Action Tool: Adds a new task into an existing project workflow."""
    t_id = create_task(project_id, name, description, priority, status, assignee)
    log_agent_action("state_change_create", "add_project_task", f"Created Task ID {t_id} for Proj {project_id}")
    return f"Successfully created task '{name}' with ID: {t_id}."

@tool
def modify_task_details(task_id: int, name: Optional[str] = None, description: Optional[str] = None, priority: Optional[str] = None, status: Optional[str] = None, assignee: Optional[str] = None) -> str:
    """Action Tool: Modifies explicit attributes of a task."""
    updates = {k: v for k, v in {"name": name, "description": description, "priority": priority, "status": status, "assignee": assignee}.items() if v is not None}
    if not updates:
        return "No modifications provided."
    
    success = update_task(task_id, **updates)
    log_agent_action("state_change_update", "modify_task_details", f"Updated Task {task_id} fields: {list(updates.keys())}")
    return f"Task {task_id} successfully updated." if success else f"Failed to update Task {task_id}."

@tool
def remove_task(task_id: int) -> str:
    """Action Tool: Permanently removes a specific task."""
    delete_task(task_id)
    log_agent_action("state_change_delete", "remove_task", f"Deleted Task ID: {task_id}")
    return f"Successfully deleted task {task_id}."

# ==========================================
# DEPENDENCY ACTIONS
# ==========================================
@tool
def establish_task_dependency(task_id: int, depends_on_task_id: int) -> str:
    """Action Tool: Sets up a dependency constraint where task_id cannot start until depends_on_task_id is finished."""
    dep_id = add_dependency(task_id, depends_on_task_id)
    log_agent_action("state_change_create", "establish_task_dependency", f"Task {task_id} now depends on {depends_on_task_id}")
    return f"Dependency established successfully (Connection ID: {dep_id})."

@tool
def break_task_dependency(dependency_id: int) -> str:
    """Action Tool: Severs a task dependency constraint mapping using its mapping link ID."""
    remove_dependency(dependency_id)
    log_agent_action("state_change_delete", "break_task_dependency", f"Severed dependency mapping link ID: {dependency_id}")
    return f"Successfully removed dependency link ID {dependency_id}."

# ==========================================
# RISK ACTIONS
# ==========================================
@tool
def register_project_risk(project_id: int, description: str, severity: str = "Low", status: str = "Open") -> str:
    """Action Tool: Log a newly identified project operational risk item."""
    r_id = add_risk(project_id, description, severity, status)
    log_agent_action("state_change_create", "register_project_risk", f"Logged Risk ID {r_id} for Proj {project_id}")
    return f"Successfully registered project risk with ID: {r_id}."

@tool
def modify_project_risk(risk_id: int, description: Optional[str] = None, severity: Optional[str] = None, status: Optional[str] = None) -> str:
    """Action Tool: Modifies an active risk profile asset's criteria attributes."""
    updates = {k: v for k, v in {"description": description, "severity": severity, "status": status}.items() if v is not None}
    if not updates:
        return "No modification profiles submitted."
    
    success = update_risk(risk_id, **updates)
    log_agent_action("state_change_update", "modify_project_risk", f"Updated Risk {risk_id} fields: {list(updates.keys())}")
    return f"Risk asset {risk_id} updated." if success else f"Failed to modify Risk asset {risk_id}."

@tool
def remove_project_risk(risk_id: int) -> str:
    """Action Tool: Deletes a tracked risk index entirely."""
    delete_risk(risk_id)
    log_agent_action("state_change_delete", "remove_project_risk", f"Deleted Risk ID: {risk_id}")
    return f"Successfully removed risk record {risk_id}."