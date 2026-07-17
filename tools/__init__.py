from .information_tools import (
    list_all_projects,
    retrieve_project_context,
    view_tasks,
    check_task_dependencies,
    view_project_risks,
    view_audit_logs,
    
    # New User & Skill Information Tools
    view_users,
    view_skills
)
from .analysis_tools import (
    analyze_task_blockers,
    calculate_project_health_score,
    classify_project_risk_profile,
    check_dependency_cycle,
    validate_task_inputs
)
from .action_tools import (
    add_new_project, modify_project_details, remove_project,
    add_project_task, modify_task_details, remove_task,
    establish_task_dependency, break_task_dependency,
    register_project_risk, modify_project_risk, remove_project_risk,
    add_new_user, modify_user_details, remove_user,
    add_new_skill, modify_skill_details, remove_skill
)
from .reporting_tools import generate_status_report

AGENT_TOOLS = [
    # Info Layer
    list_all_projects,
    retrieve_project_context,
    view_tasks,
    check_task_dependencies,
    view_project_risks,
    view_audit_logs,
    view_users,
    view_skills,
    
    # Analysis Layer
    analyze_task_blockers,
    calculate_project_health_score,
    classify_project_risk_profile,
    check_dependency_cycle,
    validate_task_inputs,
    
    # Action Layer
    add_new_project,
    modify_project_details,
    remove_project,
    add_project_task,
    modify_task_details,
    remove_task,
    establish_task_dependency,
    break_task_dependency,
    register_project_risk,
    modify_project_risk,
    remove_project_risk,
    add_new_user,
    modify_user_details,
    remove_user,
    add_new_skill,
    modify_skill_details,
    remove_skill,
    
    # Reporting Layer
    generate_status_report
]