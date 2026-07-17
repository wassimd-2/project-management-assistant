import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
# Ensure the root project directory is in the Python path for seamless imports
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph

def extract_text_content(content) -> str:
    """Safely extracts text strings from raw string data or content block lists."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif isinstance(block, str):
                text_parts.append(block)
        return "".join(text_parts)
    return str(content)

# ==========================================
# PAGE SETUP & STYLING
# ==========================================
st.set_page_config(page_title="PM Assistant Engine", page_icon="💼", layout="wide")
st.title("💼 Software Project Management Assistant")
st.caption("Deterministic Stateful Orchestration Layer powered by LangGraph & Gemini")

# Initialize Thread ID for short-term memory continuity
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = "default-university-session-1"

config = {"configurable": {"thread_id": st.session_state["thread_id"]}}

# Fetch the absolute latest current state directly from the graph engine
current_graph_state = app_graph.get_state(config)

# ==========================================
# SIDEBAR: VISUAL WORKING MEMORY (Grading Criteria Showcase)
# ==========================================
st.sidebar.header("🧠 Agent Working Memory")
st.sidebar.markdown("---")

if current_graph_state.values:
    state_vals = current_graph_state.values
    
    st.sidebar.subheader("📋 Core Workflow State")
    st.sidebar.info(f"**Current Phase:** {state_vals.get('current_workflow_state', 'Idle')}")
    
    st.sidebar.subheader("🎯 Extracted Intent")
    st.sidebar.code(state_vals.get("current_intent") or "None Identified")
    
    st.sidebar.subheader("📥 Collected Attributes")
    st.sidebar.json(state_vals.get("collected_info", {}))
    
    st.sidebar.subheader("⚠️ Missing Fields Tracked")
    missing = state_vals.get("missing_fields", [])
    if missing:
        st.sidebar.warning(f"Fields needed: {missing}")
    else:
        st.sidebar.success("No missing fields detected")
        
    st.sidebar.subheader("⚡ Last Tool Output")
    st.sidebar.text_area(
        label="", 
        value=state_vals.get("latest_tool_result") or "No recent tool calls execution data.", 
        height=100, 
        disabled=True
    )
else:
    st.sidebar.write("Start a conversation to initialize working memory streams.")

# ==========================================
# MAIN PANEL: CONVERSATION STORAGE & RENDER
# ==========================================
# Synchronize chat presentation state from the graph's persistent history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Synchronize messages from graph history if available
if current_graph_state.values and "messages" in current_graph_state.values:
    st.session_state.chat_history = current_graph_state.values["messages"]

# Render previous dialogue messages smoothly
# Render previous dialogue messages smoothly
for msg in st.session_state.chat_history:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(extract_text_content(msg.content))
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            # Sanitize the content payload before giving it to markdown
            clean_text = extract_text_content(msg.content)
            if clean_text.strip():
                st.markdown(clean_text)

# ==========================================
# HUMAN-IN-THE-LOOP INTERRUPT INTERFACE
# ==========================================
# Check if the graph's next node execution path is paused at our confirmation guard hook
is_interrupted = len(current_graph_state.next) > 0 and current_graph_state.next[0] == "confirmation_guard"

if is_interrupted:
    pending_tool = current_graph_state.values.get("pending_confirmation", "Unknown Action")
    pending_args = current_graph_state.values.get("pending_action_args", {})
    
    st.warning(f"🛑 **Human-in-the-Loop Confirmation Required!**")
    st.markdown(f"The Agent wants to execute an authorized state change operation: **`{pending_tool}`**")
    st.json(pending_args)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve & Execute Action", use_container_width=True):
            # Advance execution by passing None to tell the graph to move past the interrupt hook
            # This loop runs the graph until it hits the next interrupt or ends
            with st.spinner("Executing approved action..."):
                for event in app_graph.stream(None, config, stream_mode="values"):
                    # Optionally, you can print(event) here for debug logs
                    pass
            st.success("Action Approved and Executed!")
            st.rerun()
            
    with col2:
        if st.button("❌ Reject & Cancel Action", use_container_width=True):
            # Overwrite graph state by appending a structural cancellation notification
            app_graph.update_state(
                config, 
                {
                    "messages": [HumanMessage(content="Action denied and cancelled by the system administrator.")],
                    "current_workflow_state": "action_aborted",
                    "missing_fields": [],
                    "current_intent": None
                },
                as_node="agent" # Simulate this update coming from the agent node to cleanly clear the track
            )
            st.rerun()

# ==========================================
# CHAT LOGIC INPUT LOOP
# ==========================================
# Block new standard text submissions while an active confirmation prompt is pending
# if not is_interrupted:
if user_input := st.chat_input("Ask about projects, tasks, operational risks, or progress reports...", disabled=is_interrupted):
        
    # Instantly render user input to screen
    with st.chat_message("user"):
        st.markdown(user_input)
            
    # Dispatch input tuple payload into the LangGraph state machine tracking framework
    with st.spinner("Agent evaluating metrics..."):
        for event in app_graph.stream({"messages": [HumanMessage(content=user_input)]}, config, stream_mode="values"):
            # Run through the state iterations sequentially
            pass
                
    # Force a localized rerun to synchronize UI state with the backend graph data updates
    st.rerun()