from langchain_core.tools import tool
from app.database import get_project, get_tasks
from app.logger import log_agent_action

@tool
def generate_status_report(project_id: int) -> str:
    """
    Reporting Tool: Produces a structured text summary and handoff report of the 
    project's overall progress, task counts, and completion rates.
    """
    log_agent_action(
        intent="report_generation", 
        tool_used="generate_status_report", 
        details=f"Generating report for Project ID: {project_id}"
    )
    
    project = get_project(project_id)
    if not project:
        return f"Cannot generate report: Project ID {project_id} not found."
    
    tasks = get_tasks(project_id=project_id)
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("status") == "Done")
    
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    report = f"### Project Status Report: {project[0]['name']}\n\n"
    report += f"**Description:** {project[0]['description']}\n"
    report += f"**Overall Progress:** {progress:.1f}%\n"
    report += f"**Total Tasks:** {total_tasks} | **Completed:** {completed_tasks}\n\n"
    
    if total_tasks > completed_tasks:
        report += "**Pending Action Items:**\n"
        for t in tasks:
            if t.get("status") != "Done":
                report += f"- **[{t.get('priority')}]** {t.get('name')} *(Status: {t.get('status')})*\n"
                
    return report