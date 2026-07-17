from typing import Optional
from langchain_core.tools import tool
from app.database import (
    create_project, update_project, delete_project, get_project,
    create_task, update_task, delete_task, get_tasks,
    add_dependency, remove_dependency,
    add_risk, update_risk, delete_risk, get_incomplete_dependencies,
    create_user, update_user, delete_user,
    create_skill, update_skill, delete_skill, get_skills
)
from app.logger import log_agent_action
from dateutil import parser
from datetime import datetime
import difflib

def find_matching_skill(skill_name: str, similarity_cutoff: float = 0.6) -> Optional[dict[str, any]]:
    """
    Checks the database for an identical or highly similar skill.
    Handles:
      1. Exact case-insensitive matches ('flutter' == 'Flutter')
      2. Word-level substring matches ('Flutter App' contains 'Flutter')
      3. Fuzzy typo matching ('fluter' matches 'Flutter')
    """
    all_skills = get_skills()
    if not all_skills:
        return None

    normalized_input = skill_name.strip().lower()

    # 1. Check for exact or close case-insensitive word matching
    for skill in all_skills:
        normalized_existing = skill["skill_name"].lower()
        if normalized_input == normalized_existing:
            return skill
            
        # Match common variations like "Flutter" and "Flutter App" by checking overlapping words
        words_input = set(normalized_input.split())
        words_existing = set(normalized_existing.split())
        if words_input.intersection(words_existing):
            # Only match if they share a significant word and are short phrases
            if len(words_input) <= 2 or len(words_existing) <= 2:
                return skill

    # 2. Fuzzy match to catch typos (e.g., "fluter" -> "Flutter")
    existing_names = [s["skill_name"] for s in all_skills]
    matches = difflib.get_close_matches(skill_name, existing_names, n=1, cutoff=similarity_cutoff)
    if matches:
        matched_name = matches[0]
        for skill in all_skills:
            if skill["skill_name"] == matched_name:
                return skill

    return None

def normalize_date(date_str: str) -> str:
    """
    Intelligently parses almost any date format (1/1/2026, 2026-1-1, Jan 1 2026)
    and returns a standardized YYYY-MM-DD string.
    """
    try:
        # fuzzy=True allows it to ignore extra text (like "due date is 1/1/2026")
        dt = parser.parse(date_str, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        # Fallback: if it's completely unparseable, return the raw string 
        # or raise a custom error for the LLM to fix
        return date_str

# ==========================================
# SKILL ACTIONS
# ==========================================
@tool
def add_new_skill(skill_name: str, category: Optional[str] = None) -> str:
    """
    Action Tool: Adds a new skill to the registry. 
    Before inserting, it automatically checks for existing identical or highly similar 
    skills (like 'Flutter' vs 'Flutter App') to prevent duplicate records.
    """
    # Check if we already have this skill (or something very similar) in the DB
    existing_skill = find_matching_skill(skill_name)
    
    if existing_skill:
        return (
            f"Validation Notice: A highly similar skill already exists: '{existing_skill['skill_name']}' "
            f"(ID: '{existing_skill['skill_id']}'). To prevent duplicates, a new skill was not created. "
            f"Please use the existing ID '{existing_skill['skill_id']}' for user assignments."
        )
        
    # If it is truly a new skill, go ahead and write it to the database
    skill_id = create_skill(skill_name, category)
    log_agent_action("state_change_create", "add_new_skill", f"Created Skill ID {skill_id}: {skill_name}")
    return f"Successfully registered skill '{skill_name}' with ID: {skill_id}."

@tool
def modify_skill_details(skill_id: str, skill_name: Optional[str] = None, category: Optional[str] = None) -> str:
    """Action Tool: Modifies attributes of an existing skill in the registry."""
    updates = {k: v for k, v in {"skill_name": skill_name, "category": category}.items() if v is not None}
    if not updates:
        return "No modification arguments were provided."
    
    success = update_skill(skill_id, **updates)
    log_agent_action("state_change_update", "modify_skill_details", f"Updated Skill {skill_id} fields: {list(updates.keys())}")
    return f"Skill {skill_id} successfully updated." if success else f"Failed to update Skill {skill_id}."

@tool
def remove_skill(skill_id: str) -> str:
    """Action Tool: Permanently removes a skill from the registry."""
    delete_skill(skill_id)
    log_agent_action("state_change_delete", "remove_skill", f"Deleted Skill ID: {skill_id}")
    return f"Successfully deleted skill {skill_id}."

# ==========================================
# USER ACTIONS
# ==========================================
@tool
def add_new_user(name: str, email: str, role: Optional[str] = None, skill_id: Optional[str] = None) -> str:
    """Action Tool: Registers a new user and associates them with a skill (by name)."""
    u_id = create_user(name, email, role, skill_id)
    log_agent_action("state_change_create", "add_new_user", f"Created User ID {u_id}: {name}")
    return f"Successfully registered user '{name}' with ID: {u_id}."

@tool
def modify_user_details(user_id: int, name: Optional[str] = None, email: Optional[str] = None, role: Optional[str] = None, skill_id: Optional[str] = None) -> str:
    """Action Tool: Modifies profile fields of an existing user."""
    updates = {k: v for k, v in {"name": name, "email": email, "role": role, "skill_id": skill_id}.items() if v is not None}
    if not updates:
        return "No modification arguments were provided."
    
    success = update_user(user_id, **updates)
    log_agent_action("state_change_update", "modify_user_details", f"Updated User {user_id} fields: {list(updates.keys())}")
    return f"User {user_id} successfully updated." if success else f"Failed to update User {user_id}."

@tool
def remove_user(user_id: int) -> str:
    """Action Tool: Deletes a user profile. Automatically unassigns them from any tasks."""
    delete_user(user_id)
    log_agent_action("state_change_delete", "remove_user", f"Deleted User ID: {user_id}")
    return f"Successfully deleted user {user_id}."

# ==========================================
# PROJECT ACTIONS
# ==========================================
@tool
def add_new_project(name: str, description: str = "", status: str = "Planning", due_date: str = None) -> str:
    """Action Tool: Creates a new project profile."""
    clean_due_date = normalize_date(due_date) if due_date else None
    p_id = create_project(name, description, status, clean_due_date)
    log_agent_action("state_change_create", "add_new_project", f"Created Proj ID {p_id}: {name}")
    return f"Successfully created project '{name}' with ID: {p_id}."

@tool
def modify_project_details(project_id: int, name: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None, due_date: Optional[str] = None) -> str:
    """Action Tool: Modifies attributes of an existing project profile."""
    clean_due_date = normalize_date(due_date) if due_date else None
    updates = {k: v for k, v in {"name": name, "description": description, "status": status, "due_date": clean_due_date}.items() if v is not None}
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
def add_project_task(project_id: int, name: str, description: str = "", priority: str = "Medium", status: str = "To Do", assignee_id: Optional[int] = None, due_date: str = None) -> str:
    """Action Tool: Adds a new task into an existing project workflow with an optional assignee user ID."""
    clean_due_date = normalize_date(due_date) if due_date else None
    # Enforce Project Deadline Boundaries
    if clean_due_date:
        project_list = get_project(project_id)
        if project_list and project_list[0].get("due_date"):
            proj_due_date = project_list[0]["due_date"]
            if clean_due_date > proj_due_date:
                return (
                    f"Action Blocked: Cannot set task due date to '{clean_due_date}'. "
                    f"It exceeds the project's absolute deadline of '{proj_due_date}'."
                )
    t_id = create_task(project_id, name, description, priority, status, assignee_id, clean_due_date)
    log_agent_action("state_change_create", "add_project_task", f"Created Task ID {t_id} for Proj {project_id}")
    return f"Successfully created task '{name}' with ID: {t_id}."

@tool
def modify_task_details(task_id: int, name: Optional[str] = None, description: Optional[str] = None, priority: Optional[str] = None, status: Optional[str] = None, assignee_id: Optional[int] = None, due_date: Optional[str] = None) -> str:
    """Action Tool: Modifies explicit attributes of a task."""
    clean_due_date = normalize_date(due_date) if due_date else None
    updates = {k: v for k, v in {"name": name, "description": description, "priority": priority, "status": status, "assignee_id": assignee_id, "due_date": clean_due_date}.items() if v is not None}
    if not updates:
        return "No modifications provided."
    # Enforce Project Deadline Boundaries on Modification
    if "due_date" in updates:
        task_list = get_tasks(task_id=task_id)
        if not task_list:
            return f"Error: Task with ID {task_id} not found."
        project_id = task_list[0]["project_id"]
        project_list = get_project(project_id)
        if project_list and project_list[0].get("due_date"):
            proj_due_date = project_list[0]["due_date"]
            if updates["due_date"] > proj_due_date:
                return (
                    f"Action Blocked: Cannot update task due date to '{updates['due_date']}'. "
                    f"It exceeds the project's absolute deadline of '{proj_due_date}'."
                )
    # Check if the incoming status modification is targeting 'In Progress'
    if updates.get("status") == "In Progress":
        # Check database for blocking parent tasks
        incomplete_tasks = get_incomplete_dependencies(task_id)
        if incomplete_tasks:
            blocking_list = ", ".join([f"'{task_name}'" for task_name in incomplete_tasks])
            return (
                f"Action Blocked: Cannot set Task {task_id} to 'In Progress'. "
                f"It depends on the following incomplete tasks: {blocking_list}. "
                f"Please notify the user about these blockers."
            )
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