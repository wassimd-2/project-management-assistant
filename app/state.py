from typing import TypedDict, Annotated, Any, Dict, List, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # ==========================================
    # 1. SHORT-TERM MEMORY
    # ==========================================
    # The `add_messages` annotation ensures that new messages are appended 
    # to the list rather than overwriting the whole list.
    messages: Annotated[list, add_messages]
    user_name: Optional[str]

    # ==========================================
    # 2. WORKING MEMORY (Mandatory Fields)
    # ==========================================
    # The current goal the user is trying to achieve (e.g., "create_task")
    current_intent: Optional[str]
    
    # Dictionary mapping field names to values extracted so far
    # e.g., {"task_name": "Setup DB", "priority": "High"}
    collected_info: Dict[str, Any]
    
    # List of required fields still missing for the current intent
    missing_fields: List[str]
    
    # Stores the action name pending explicit user confirmation
    # If None, no confirmation is pending.
    pending_confirmation: Optional[str]
    
    # Stores the arguments for the pending action while waiting for confirmation
    pending_action_args: Optional[Dict[str, Any]]
    
    # The output from the last executed tool
    latest_tool_result: Optional[str]
    
    # Explicit workflow tracking (e.g., "collecting_info", "awaiting_confirmation", "executing")
    current_workflow_state: str