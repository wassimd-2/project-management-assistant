from typing import Dict, Any, List, Tuple
from app.state import AgentState

# Define required fields for state-changing operations
REQUIRED_FIELDS = {
    # Projects
    "add_new_project": ["name"],
    "modify_project_details": ["project_id"],
    "remove_project": ["project_id"],
    
    # Tasks
    "add_project_task": ["project_id", "name"],
    "modify_task_details": ["task_id"],
    "remove_task": ["task_id"],
    
    # Dependencies
    "establish_task_dependency": ["task_id", "depends_on_task_id"],
    "break_task_dependency": ["task_id", "depends_on_task_id"],
    
    # Risks
    "register_project_risk": ["project_id", "description"],
    "modify_project_risk": ["risk_id"],
    "remove_project_risk": ["risk_id"],
    
    # Assignments
    "assign_task": ["task_id", "assignee_name"]
}

def analyze_working_memory(state: AgentState) -> Dict[str, Any]:
    """
    Populates working memory and automatically flushes stale data 
    if a context/intent switch is detected.
    """
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    updates = {}
    
    # Check if a tool is being called
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call["name"]
        args = dict(tool_call["args"])

        # --- THE FIX: DETECT CONTEXT SWITCH ---
        current_intent = state.get("current_intent")
        
        # If the new tool is different from the previous intent, clear everything!
        if current_intent and tool_name != current_intent:
            print(f"DEBUG: Intent switch detected ({current_intent} -> {tool_name}). Flushing stale state.")
            updates["pending_confirmation"] = None
            updates["pending_action_args"] = None
            updates["missing_fields"] = []
            updates["current_workflow_state"] = "collecting_info" # Reset to start flow
        
        # --- Update with new data ---
        updates["current_intent"] = tool_name
        updates["collected_info"] = args

        # --- Evaluate Missing Fields ---
        if tool_name in REQUIRED_FIELDS:
            missing = [
                field for field in REQUIRED_FIELDS[tool_name] 
                if field not in args or args[field] is None or str(args[field]).strip() == ""
            ]
            updates["missing_fields"] = missing
            
            # Change workflow state
            if missing:
                updates["current_workflow_state"] = "collecting_info"
            else:
                updates["current_workflow_state"] = "ready"
                # If we are ready, we prepare for the confirmation step
                updates["pending_confirmation"] = tool_name
                updates["pending_action_args"] = args
                
    return updates