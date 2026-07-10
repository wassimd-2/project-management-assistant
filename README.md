# 💼 AI Project Management Assistant

**A Deterministic, Stateful Orchestration Agent powered by LangGraph and Google Gemini.**

The AI Project Management Assistant is an AI-powered agent designed to help users manage projects through natural language interactions. It uses **Google Gemini** as the reasoning engine, **LangGraph** for deterministic workflow orchestration, **Streamlit** for the web interface, and **SQLite** for persistent project data storage.

The system is designed around a stateful graph architecture that ensures reliable execution, strict operational boundaries, and predictable behavior. Instead of relying on free-form generation, the assistant combines an LLM with deterministic tools to provide grounded and reliable project management operations.

The assistant can:

- Create and manage projects
- Create and update tasks
- Assign task priorities
- Track task status
- Manage task dependencies
- Identify project risks
- Calculate project progress
- Generate project summaries

The system does **not** use RAG or a vector database. All project information is stored in SQLite, while project rules and configurations are stored using structured data.

---

# ✨ Core Features

## Deterministic Workflow

Powered by LangGraph, the assistant follows a controlled execution flow instead of unpredictable text generation.

The workflow ensures:

- Intent classification before execution
- Correct tool selection
- Reliable state transitions
- Grounded responses
- Logged agent decisions

---

## Human-in-the-Loop (HITL)

Any action that modifies project state requires explicit user confirmation before execution.

Examples:

- Creating projects
- Creating tasks
- Updating task status
- Adding risks
- Creating dependencies

The agent pauses execution, requests confirmation, and only continues after approval.

---

## Scope Guardrails

The assistant operates strictly within the project management domain.

It refuses unrelated requests such as:

- General trivia
- Weather questions
- Unrelated programming tasks
- Requests outside available project tools

---

## Dual Interfaces

The application provides two ways to interact with the agent.

### Web Dashboard

A Streamlit-based interface for normal users.

Features:

- Chat-based interaction
- Project management operations
- Reactive state viewing


### CLI Debug Interface

A lightweight terminal interface for testing and debugging.

---

## Environment Agnostic

The application is fully containerized using Docker, allowing reliable deployment across different operating systems.

---

# 🏗️ Project Architecture

```text
project-management-assistant/

├── app/
│   ├── graph.py              # LangGraph state machine and LLM routing
│   ├── llm.py                # Gemini API connection and model configuration
│   ├── state.py              # Graph state and memory definitions
│   ├── database.py           # SQLite database interface
│   ├── logger.py             # Logging configuration
│   └── validation.py         # Input validation logic
│
├── tools/
│   ├── information_tools.py  # Data retrieval operations
│   ├── analysis_tools.py     # Calculations and validation
│   ├── action_tools.py       # State-changing operations
│   └── reporting_tools.py    # Project reporting
│
├── ui/
│   └── streamlit_app.py      # Web dashboard interface
│
├── storage/
│   └── project_manager.db
│
├── logs/
│   └── agent.log
│
├── tests/
│   └── evaluation.md
│
├── .env                      # User-created API keys
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py                    # CLI debug interface
└── README.md
```

---

# 🔄 Agent Workflow

The assistant follows a controlled execution workflow:

1. User submits a request.
2. The LLM analyzes and classifies the intent.
3. LangGraph determines the required workflow path.
4. The appropriate tool is selected.
5. If the action changes project state, confirmation is requested.
6. After confirmation, the tool executes.
7. Results are returned to the user.
8. Intent, tool usage, and execution details are logged.

---

# 🛠️ Implemented Tools

## Information Tool

Used for retrieving existing project information.

Capabilities:

- Retrieve projects
- Retrieve tasks
- Retrieve risks
- Retrieve dependencies

---

## Analysis Tool

Used for calculations and project evaluation.

Capabilities:

- Validate task inputs
- Calculate project progress
- Calculate project risk scores

---

## Action Tool

Used for operations that modify project state.

Capabilities:

- Create and update project
- Create and update task
- Create risk
- Add dependency

All state-changing actions require explicit user confirmation.

---

## Reporting Tool

Used for generating project insights.

Capabilities:

- Generate project summaries
- Provide progress reports

---

# 🧠 Memory System

The assistant uses LangGraph state management for memory.

## Short-Term Memory

Maintains conversation context during the current session.

Examples:

- Previous user messages
- Current workflow state
- Recent tool results


## Working Memory

Stores important information needed during execution.

Examples:

- Current project
- Selected task
- Active operation context

---

# 🗄️ Data Storage

Project data is stored using SQLite.

Stored information includes:

- Projects
- Tasks
- Risks
- Dependencies
- Project state information

The system does not use:

- Vector databases
- Retrieval-Augmented Generation (RAG)

---

# 📝 Logging

The system records:

- Detected user intent
- Selected tools
- Confirmation actions
- Execution results
- Errors

Logs are stored in:

```text
logs/agent.log
```

---

# 🚀 Quick Start (Docker - Recommended)

Docker provides the most reliable way to run the application by creating a consistent Python environment.

## Prerequisites

- Docker Desktop installed and running
- A valid Google Gemini API key

---

## 1. Configure Environment Variables

Create a `.env` file in the project root:

```text
GEMINI_API_KEY="your_google_gemini_api_key_here"
```

---

## 2. Build and Run the Application

```bash
docker-compose up --build
```

---

## 3. Access the Dashboard

Open:

```text
http://localhost:8501
```

---

## Stop the Application

Press:

```text
Ctrl + C
```

or run:

```bash
docker-compose down
```

---

# 💻 Local Development Setup

If Docker is not used, the application can run directly.

## 1. Create Virtual Environment

Python 3.12+ is recommended.

```bash
python -m venv .venv
```

Activate:

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Run the Interfaces

### Web Interface

```bash
streamlit run ui/streamlit_app.py
```

### CLI Debug Interface

```bash
python run.py
```

---

# 💬 Example Prompts

Create a new project:

```text
Create a new project called AI Research.
```

Create a task:

```text
Create a High priority task for Alice due tomorrow.
```

Retrieve tasks:

```text
Show all pending tasks.
```

Analyze progress:

```text
Calculate project progress.
```

Generate reports:

```text
Generate a project summary.
```

Identify risks:

```text
Identify project risks.
```

---

# 📦 Technologies

- Python
- LangGraph
- LangChain
- Google Gemini API
- Streamlit
- SQLite
- Docker

---

# ✅ Requirements Covered

- LangGraph orchestration
- Stateful agent architecture
- Gemini API reasoning
- Streamlit web interface
- CLI debugging interface
- SQLite persistent storage
- Four tool categories
- Short-term memory
- Working memory
- Explicit workflow states
- Human-in-the-loop confirmation
- Scope guardrails
- Intent logging
- Tool usage logging
- Docker deployment
- No RAG or vector database