from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from app.state import AgentState
from app.llm import get_llm
from app.validation import analyze_working_memory
from tools import AGENT_TOOLS

# Identify all action tools that require human-in-the-loop confirmation
ACTION_TOOL_NAMES = {
    "add_new_project", "modify_project_details", "remove_project",
    "add_project_task", "modify_task_details", "remove_task",
    "establish_task_dependency", "break_task_dependency",
    "register_project_risk", "modify_project_risk", "remove_project_risk"
}

# ==========================================
# NODES
# ==========================================
def call_agent(state: AgentState) -> Dict[str, Any]:
    """Executes the LLM core logic."""
    llm = get_llm()
    
    # Inject working memory explicitly into system prompt context for grounding
    # Inside app/graph.py -> call_agent node function:
    system_prompt = (
    "You are an elite, dedicated Project Management Assistant.\n"
    "CRITICAL BOUNDARY: You only assist with project management topics (projects, tasks, dependencies, risks, and reports).\n"
    "If the user asks about anything outside of this topic (e.g., cooking, general coding unrelated to this PM data, jokes, history, weather, etc.), "
    "you MUST refuse the request politely and clearly state that you are only a Project Management Assistant.\n\n"
    f"Current Intent: {state.get('current_intent')}\n"
    f"Missing Fields: {state.get('missing_fields')}\n\n"
    "If mandatory information is missing to perform an authorized action, do not call the tool. "
    "Instead, ask the user clearly to provide the missing fields."
    )
    
    # Execute LLM call
    response = llm.invoke([{"role": "system", "content": system_prompt}] + state["messages"])
    
    return {"messages": [response], "current_workflow_state": "agent_evaluated"}


def memory_gatekeeper_node(state: AgentState) -> Dict[str, Any]:
    """Runs data validation to update Working Memory values."""
    updates = analyze_working_memory(state)
    return updates


def confirmation_guard_node(state: AgentState) -> Dict[str, Any]:
    """
    A placeholder node used as an interruption hook. 
    Execution pauses here if an action requires confirmation.
    """
    # Pull the target tool call details to save in holding memory
    last_msg = state["messages"][-1]
    tool_call = last_msg.tool_calls[0]
    
    return {
        "pending_confirmation": tool_call["name"],
        "pending_action_args": tool_call["args"],
        "current_workflow_state": "awaiting_confirmation"
    }

# Build out the standard prebuilt tool execution node
tool_node = ToolNode(AGENT_TOOLS)

# ==========================================
# ROUTING LOGIC
# ==========================================
def route_after_agent(state: AgentState) -> Literal["memory_gatekeeper", "__end__"]:
    """Routes execution to validation block if tool calls are requested."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "memory_gatekeeper"
    return END


def route_after_validation(state: AgentState) -> Literal["confirmation_guard", "tools", "__end__"]:
    """Evaluates constraints to handle missing fields or process approvals."""
    # Scenario A: Block execution if mandatory fields are missing
    if state.get("missing_fields"):
        return END
        
    last_message = state["messages"][-1]
    tool_name = last_message.tool_calls[0]["name"]
    
    # Scenario B: If it's a structural mutation, route to the confirmation guard
    if tool_name in ACTION_TOOL_NAMES:
        return "confirmation_guard"
        
    # Scenario C: Read-only info/analysis tools bypass confirmations completely
    return "tools"

# ==========================================
# GRAPH COMPILATION
# ==========================================
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("agent", call_agent)
workflow.add_node("memory_gatekeeper", memory_gatekeeper_node)
workflow.add_node("confirmation_guard", confirmation_guard_node)
workflow.add_node("tools", tool_node)

# Set Up Edge Constraints
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", route_after_agent)
workflow.add_conditional_edges("memory_gatekeeper", route_after_validation)

# Once tools finish executing, return loop to the agent to synthesize response
workflow.add_edge("tools", "agent")
# Once a confirmation is cleared by the user, it goes directly into the tools node
workflow.add_edge("confirmation_guard", "tools")

# Compile the final graph topology
# Interrupt execution *before* reaching the confirmation guard node
# Ensure compile looks like this:
app_graph = workflow.compile(
    checkpointer=MemorySaver(), 
    interrupt_before=["confirmation_guard"]
)