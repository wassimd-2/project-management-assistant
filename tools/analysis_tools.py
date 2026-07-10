import json
from langchain_core.tools import tool
from app.database import get_tasks, get_risks, get_connection
from app.logger import log_agent_action

# Helper function for recursive graph traversal in cyclic checks
def _is_reachable(start_id: int, target_id: int, visited=None) -> bool:
    if visited is None:
        visited = set()
    if start_id == target_id:
        return True
    visited.add(start_id)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        # Find all tasks that start_id depends on
        cursor.execute("SELECT depends_on_task_id FROM dependencies WHERE task_id = ?", (start_id,))
        neighbors = [row['depends_on_task_id'] for row in cursor.fetchall()]
        
    for neighbor in neighbors:
        if neighbor not in visited:
            if _is_reachable(neighbor, target_id, visited):
                return True
    return False


@tool
def analyze_task_blockers(task_id: int) -> str:
    """
    Analysis Tool [Checks Constraints]: Examines a task's immediate dependencies 
    to see if any prerequisite tasks are not yet marked as 'Done'.
    """
    log_agent_action(intent="constraint_analysis", tool_used="analyze_task_blockers", details=f"Task ID: {task_id}")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT t.id, t.name, t.status FROM tasks t
            JOIN dependencies d ON t.id = d.depends_on_task_id
            WHERE d.task_id = ?
        """
        cursor.execute(query, (task_id,))
        dependencies = [dict(row) for row in cursor.fetchall()]

    blocking_tasks = [t for t in dependencies if t["status"] != "Done"]
    is_blocked = len(blocking_tasks) > 0
    
    return json.dumps({
        "task_id": task_id,
        "is_blocked": is_blocked,
        "blocking_tasks": blocking_tasks
    })


@tool
def calculate_project_health_score(project_id: int) -> str:
    """
    Analysis Tool [Calculates a Score]: Computes a deterministic numeric health score (0-100) 
    for a project based on task completion rates, high-priority backlogs, and active risks.
    """
    log_agent_action(intent="score_calculation", tool_used="calculate_project_health_score", details=f"Proj ID: {project_id}")
    
    tasks = get_tasks(project_id=project_id)
    risks = get_risks(project_id=project_id)
    
    if not tasks:
        return json.dumps({"project_id": project_id, "health_score": 100, "reason": "No tasks assigned yet. Perfect clean slate."})
    
    # Base configuration score
    score = 100
    deductions = []
    
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["status"] == "Done")
    completion_rate = completed_tasks / total_tasks
    
    # Rule 1: Task completion ratio (Up to 30 point deduction if 0% complete)
    task_penalty = int((1 - completion_rate) * 30)
    if task_penalty > 0:
        score -= task_penalty
        deductions.append(f"Unfinished tasks penalty: -{task_penalty}")
        
    # Rule 2: Overdue or High Priority Stuck Tasks
    high_priority_stuck = sum(1 for t in tasks if t["priority"] == "High" and t["status"] != "Done")
    if high_priority_stuck > 0:
        stuck_penalty = min(high_priority_stuck * 8, 25)
        score -= stuck_penalty
        deductions.append(f"High priority uncompleted tasks: -{stuck_penalty}")

    # Rule 3: High Severity Active Risks
    high_risks = sum(1 for r in risks if r["severity"] == "High" and r["status"] == "Open")
    if high_risks > 0:
        risk_penalty = min(high_risks * 15, 30)
        score -= risk_penalty
        deductions.append(f"Unmitigated High risks: -{risk_penalty}")
        
    final_score = max(0, score)
    
    return json.dumps({
        "project_id": project_id,
        "health_score": final_score,
        "metrics": {
            "completion_rate": f"{completion_rate*100:.1f}%",
            "high_priority_backlog": high_priority_stuck,
            "open_high_risks": high_risks
        },
        "deductions_applied": deductions
    })


@tool
def classify_project_risk_profile(project_id: int) -> str:
    """
    Analysis Tool [Classifies a Case]: Evaluates structural data boundaries to categorize 
    the project's threat posture into a explicit case classification: 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'.
    """
    log_agent_action(intent="case_classification", tool_used="classify_project_risk_profile", details=f"Proj ID: {project_id}")
    
    risks = get_risks(project_id=project_id)
    tasks = get_tasks(project_id=project_id)
    
    open_high_risks = sum(1 for r in risks if r["severity"] == "High" and r["status"] == "Open")
    open_med_risks = sum(1 for r in risks if r["severity"] == "Medium" and r["status"] == "Open")
    
    # Check for blocking loops or high concentration of bottlenecks
    blocked_count = 0
    for t in tasks:
        blocker_json = analyze_task_blockers.invoke({"task_id": t["id"]})
        if json.loads(blocker_json)["is_blocked"]:
            blocked_count += 1

    # Deterministic Categorization Matrix
    if open_high_risks >= 3 or (open_high_risks >= 1 and blocked_count > (len(tasks) * 0.5)):
        classification = "CRITICAL"
    elif open_high_risks >= 1 or open_med_risks >= 3 or blocked_count > 2:
        classification = "HIGH"
    elif open_med_risks >= 1 or blocked_count > 0:
        classification = "MEDIUM"
    else:
        classification = "LOW"
        
    return json.dumps({
        "project_id": project_id,
        "risk_profile_classification": classification,
        "indicators": {
            "open_high_risks": open_high_risks,
            "open_medium_risks": open_med_risks,
            "blocked_tasks_count": blocked_count
        }
    })


@tool
def check_dependency_cycle(task_id: int, depends_on_task_id: int) -> str:
    """
    Analysis Tool [Applies Deterministic Diagnostic Rules]: Diagnostic check executing 
    before building dependencies. Validates if making task_id rely on depends_on_task_id 
    creates a cyclic loop.
    """
    log_agent_action(intent="diagnostic_rule_check", tool_used="check_dependency_cycle", details=f"Link request: {task_id} -> {depends_on_task_id}")
    
    if task_id == depends_on_task_id:
        return json.dumps({"allowed": False, "reason": "A task cannot depend on itself."})
    
    # If the target task (depends_on_task_id) already recursively depends on our current task (task_id),
    # adding this relationship would create an infinite loop deadlock.
    cycle_detected = _is_reachable(start_id=depends_on_task_id, target_id=task_id)
    
    return json.dumps({
        "allowed": not cycle_detected,
        "cycle_detected": cycle_detected,
        "reason": "Cycle detected! This operation is blocked to protect network graph validity." if cycle_detected else "No logical cycles found. Safe to connect."
    })


@tool
def validate_task_inputs(priority: str, status: str) -> str:
    """
    Analysis Tool [Validates Inputs]: Validates string inputs against authorized domain system constraints
    to catch typos or bad parameters before executing downstream writes.
    """
    log_agent_action(intent="input_validation", tool_used="validate_task_inputs", details=f"P: {priority}, S: {status}")
    
    VALID_PRIORITIES = {"Low", "Medium", "High"}
    VALID_STATUSES = {"To Do", "In Progress", "Done"}
    
    errors = []
    if priority not in VALID_PRIORITIES:
        errors.append(f"Invalid priority '{priority}'. Must be one of: {list(VALID_PRIORITIES)}")
    if status not in VALID_STATUSES:
        errors.append(f"Invalid status '{status}'. Must be one of: {list(VALID_STATUSES)}")
        
    return json.dumps({
        "is_valid": len(errors) == 0,
        "errors": errors
    })