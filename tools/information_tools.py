import json
from typing import Optional
from langchain_core.tools import tool
from app.database import (
    get_project, get_tasks, get_dependencies, get_risks, get_logs,
    get_users, get_skills
)
from app.logger import log_agent_action

# ==========================================
# PROJECT INFORMATION TOOLS
# ==========================================
@tool
def list_all_projects() -> str:
    """
    Information Tool: Retrieves a list of all active projects in the system.
    """
    log_agent_action(intent="information_retrieval", tool_used="list_all_projects")
    projects = get_project()
    return json.dumps(projects, default=str)

@tool
def retrieve_project_context(project_id: int) -> str:
    """
    Information Tool: Retrieves the complete structural profile of a project 
    including its basic info, all tasks, and associated risks.
    """
    log_agent_action(intent="information_retrieval", tool_used="retrieve_project_context", details=f"ID: {project_id}")
    project = get_project(project_id)
    if not project:
        return f"Error: Project with ID {project_id} not found."
    
    return json.dumps({
        "project": project[0],
        "tasks": get_tasks(project_id=project_id),
        "risks": get_risks(project_id=project_id)
    }, default=str)

# ==========================================
# TASK INFORMATION TOOLS
# ==========================================
@tool
def view_tasks(task_id: Optional[int] = None, project_id: Optional[int] = None) -> str:
    """
    Information Tool: Retrieves tasks. Provide task_id for a single task, 
    project_id to filter by project, or neither to get all tasks.
    """
    log_agent_action(intent="information_retrieval", tool_used="view_tasks", details=f"task_id: {task_id}, proj_id: {project_id}")
    tasks = get_tasks(task_id=task_id, project_id=project_id)
    return json.dumps(tasks, default=str)

@tool
def check_task_dependencies(task_id: int) -> str:
    """
    Information Tool: Retrieves all parent tasks that the specified task directly depends on.
    """
    log_agent_action(intent="information_retrieval", tool_used="check_task_dependencies", details=f"Task ID: {task_id}")
    deps = get_dependencies(task_id)
    return json.dumps(deps, default=str)

# ==========================================
# RISK INFORMATION TOOLS
# ==========================================
@tool
def view_project_risks(project_id: Optional[int] = None) -> str:
    """
    Information Tool: Retrieves tracked project risks. Provide a project_id 
    to filter by project, or leave empty to view all system risks.
    """
    log_agent_action(intent="information_retrieval", tool_used="view_project_risks", details=f"Project ID: {project_id}")
    risks = get_risks(project_id=project_id)
    return json.dumps(risks, default=str)

# ==========================================
# USER & SKILL INFORMATION TOOLS
# ==========================================
@tool
def view_users(user_id: Optional[int] = None) -> str:
    """
    Information Tool: Retrieves registered users. Provide user_id for a single user's 
    profile details, or leave empty to view all users registered in the system.
    """
    log_agent_action(intent="information_retrieval", tool_used="view_users", details=f"User ID: {user_id}")
    users = get_users(user_id=user_id)
    return json.dumps(users, default=str)

@tool
def view_skills(skill_id: Optional[str] = None) -> str:
    """
    Information Tool: Retrieves registered skills from the directory. Provide a 
    skill_id (UUID string) to view details for a specific skill, or leave empty to list all skills.
    """
    log_agent_action(intent="information_retrieval", tool_used="view_skills", details=f"Skill ID: {skill_id}")
    skills = get_skills(skill_id=skill_id)
    return json.dumps(skills, default=str)

# ==========================================
# AUDIT & SYSTEM TOOLS
# ==========================================
@tool
def view_audit_logs(limit: int = 20) -> str:
    """
    Information Tool: Fetches recent intent and tool execution logs for monitoring system activity.
    """
    log_agent_action(intent="information_retrieval", tool_used="view_audit_logs", details=f"Limit: {limit}")
    return json.dumps(get_logs(limit=limit), default=str)