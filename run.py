import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from app.graph import app_graph

# Load environment variables from .env file
load_dotenv()

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

def print_agent_response(state_values):
    """Helper to cleanly display the agent's final text in the terminal."""
    if "messages" in state_values and state_values["messages"]:
        last_message = state_values["messages"][-1]
        if hasattr(last_message, "content") and last_message.content and last_message.type == "ai":
            # Extract clean text instead of printing the raw list object
            clean_text = extract_text_content(last_message.content)
            if clean_text.strip():
                print(f"\n🤖 Assistant: {clean_text}")

def run_terminal_cli():
    print("=" * 60)
    print("💼 WELCOME TO THE PROJECT MANAGEMENT ASSISTANT CLI")
    print("=" * 60)
    print("Type your requests below. Type 'exit' or 'quit' to close.")
    print("Try: 'Create a project named Alpha' or 'Check health for project 1'")
    print("-" * 60)

    # Thread configuration for session memory tracking
    config = {"configurable": {"thread_id": "terminal-test-session"}}

    while True:
        try:
            # 1. Fetch current graph state to see if it's waiting for an interrupt
            current_state = app_graph.get_state(config)
            
            # Check if we are paused at the confirmation guard
            if current_state.next and current_state.next[0] == "confirmation_guard":
                pending_tool = current_state.values.get("pending_confirmation")
                pending_args = current_state.values.get("pending_action_args")
                
                print(f"\n🛑 [HUMAN-IN-THE-LOOP INTERRUPT]")
                print(f"The Agent wants to execute: {pending_tool}")
                print(f"Arguments: {pending_args}")
                choice = input("Approve this database state change? (yes/no): ").strip().lower()
                
                if choice in ['yes', 'y']:
                    # Passing None tells LangGraph to resume past the interruption hook
                    print("⚡ Action approved. Resuming execution chain...")
                    events = app_graph.stream(None, config, stream_mode="values")
                    for event in events:
                        final_values = event
                    print_agent_response(final_values)
                else:
                    # Inject a cancellation message into the state history to abort cleanly
                    print("❌ Action rejected. Informing the agent...")
                    app_graph.update_state(
                        config,
                        {
                            "messages": [HumanMessage(content="Action denied and cancelled by the system administrator.")],
                            "current_workflow_state": "action_aborted",
                            "missing_fields": [],
                            "current_intent": None
                        },
                        as_node="agent"
                    )
                continue

            # 2. Standard Chat Input Loop
            user_input = input("\n👤 You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            # Stream user payload into the state graph
            payload = {"messages": [HumanMessage(content=user_input)]}
            events = app_graph.stream(payload, config, stream_mode="values")
            
            # Process the execution frames to track the final output value
            final_values = {}
            for event in events:
                final_values = event
            
            # Print the text response if the graph didn't hit an interrupt
            print_agent_response(final_values)

        except KeyboardInterrupt:
            print("\nSession aborted.")
            break
        except Exception as e:
            print(f"\n⚠️ System Error: {e}")

if __name__ == "__main__":
    # Quick safety verification to ensure the API key is present before running
    if not os.getenv("GEMINI_API_KEY"):
        print("CRITICAL: GEMINI_API_KEY is not set in your .env file!")
    else:
        run_terminal_cli()