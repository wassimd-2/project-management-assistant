import os
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import AGENT_TOOLS

def get_llm():
    """
    Initializes the Gemini model using environment variables 
    and binds the master tool suite.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: GEMINI_API_KEY environment variable is missing.")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=api_key,
        temperature=0.2 # Low temperature for reliable, deterministic tool calling
    )
    
    # Bind the tools so the model knows it can call them
    return llm.bind_tools(AGENT_TOOLS)