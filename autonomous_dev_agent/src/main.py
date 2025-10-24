"""
Main application for the Autonomous Software Development Agent.
"""
from typing import Dict, Any, List, Optional
import os
import argparse

from autonomous_dev_agent.src.agents.planning_agent import PlanningAgent
from autonomous_dev_agent.src.agents.coding_agent import CodingAgent
from autonomous_dev_agent.src.agents.testing_agent import TestingAgent
from autonomous_dev_agent.src.agents.debugging_agent import DebuggingAgent
from autonomous_dev_agent.src.agents.documentation_agent import DocumentationAgent
from autonomous_dev_agent.src.workflows.development_workflow import DevelopmentWorkflow
from autonomous_dev_agent.src.utils.version_control import VersionControlManager
from autonomous_dev_agent.src.utils.interactive_learning import InteractiveLearningSystem
from autonomous_dev_agent.src.config.config import settings


def create_development_workflow(workflow_id: str) -> DevelopmentWorkflow:
    """
    Create a development workflow with all agents.
    
    Args:
        workflow_id: Unique identifier for the workflow
        
    Returns:
        Configured development workflow
    """
    # Create workflow
    workflow = DevelopmentWorkflow(workflow_id)
    
    # Create and add agents
    planning_agent = PlanningAgent()
    coding_agent = CodingAgent()
    testing_agent = TestingAgent()
    debugging_agent = DebuggingAgent()
    documentation_agent = DocumentationAgent()
    
    workflow.add_agent(planning_agent)
    workflow.add_agent(coding_agent)
    workflow.add_agent(testing_agent)
    workflow.add_agent(debugging_agent)
    workflow.add_agent(documentation_agent)
    
    # Build workflow graph
    workflow.build_graph()
    
    return workflow


def process_requirements(description: str, workflow_id: str = "default") -> Dict[str, Any]:
    """
    Process natural language requirements through the development workflow.
    
    Args:
        description: Natural language description of requirements
        workflow_id: Unique identifier for the workflow
        
    Returns:
        Results of the development process
    """
    # Create workflow
    workflow = create_development_workflow(workflow_id)
    
    # Process requirements
    result = workflow.run({
        "description": description,
        "current_agent_id": "planning_agent"
    })
    
    # Add workflow state to result
    result["workflow_state"] = workflow.get_state()
    
    return result


def main():
    """
    Main entry point for the application.
    """
    parser = argparse.ArgumentParser(description="Autonomous Software Development Agent")
    parser.add_argument("--requirements", type=str, help="Path to requirements file")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--workflow-id", type=str, default="default", help="Workflow ID")
    parser.add_argument("--vcs", type=str, choices=["github", "gitlab", "none"], default="none", help="Version control system")
    parser.add_argument("--dry-run", action="store_true", help="Run without external API calls (LLMs, VCS)")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Read requirements
    if args.requirements:
        with open(args.requirements, "r") as f:
            description = f.read()
    else:
        description = input("Enter requirements description: ")
    
    # Apply dry-run flag
    if args.dry_run:
        os.environ["DRY_RUN"] = "true"
        # Reload settings to pick up the environment variable
        from autonomous_dev_agent.src.config.config import settings
        settings.DRY_RUN = True

    # Process requirements
    result = process_requirements(description, args.workflow_id)
    
    # Handle version control if specified
    if args.vcs != "none":
        vcs_manager = VersionControlManager(provider=args.vcs)
        
        # Create feature branch
        feature_name = f"{args.workflow_id}"
        branch_result = vcs_manager.create_feature_branch(feature_name)
        branch_ref = f"feature/{feature_name}"
        print(f"Created feature branch: {branch_ref}")
        
        # Commit code changes
        files = {}
        for code_snippet in result.get("workflow_state", {}).code_snippets:
            if code_snippet.file_path:
                files[code_snippet.file_path] = code_snippet.code
        
        commit_results = vcs_manager.commit_code_changes(
            files=files,
            commit_message=f"Implement feature: {args.workflow_id}",
            branch=branch_ref
        )
        print(f"Committed {len(files)} files to {branch_ref}")
        
        # Create pull request
        pr_result = vcs_manager.create_pull_request(
            title=f"Feature: {args.workflow_id}",
            description=f"Automated PR for feature: {args.workflow_id}",
            feature_branch=branch_ref
        )
        print(f"Created pull request: {pr_result.get('html_url', pr_result)}")
    
    # Save results
    with open(os.path.join(args.output, "result.txt"), "w") as f:
        f.write(f"Workflow ID: {args.workflow_id}\n\n")
        f.write(f"Requirements:\n{description}\n\n")
        f.write("Results:\n")
        f.write(f"Status: {result.get('status', 'unknown')}\n")
        workflow_state = result.get('workflow_state', {})
        if isinstance(workflow_state, dict):
            f.write(f"Current step: {workflow_state.get('current_step', 'unknown')}\n")
            
            # Write requirements
            f.write("\nRequirements:\n")
            requirements = workflow_state.get('requirements', [])
            for req in requirements:
                if isinstance(req, dict):
                    f.write(f"- {req.get('id', 'unknown')}: {req.get('description', 'unknown')}\n")
                else:
                    f.write(f"- {req.id}: {req.description}\n")
        else:
            f.write(f"Current step: {workflow_state.current_step}\n")
            
            # Write requirements
            f.write("\nRequirements:\n")
            for req in workflow_state.requirements:
                f.write(f"- {req.id}: {req.description}\n")
        
        # Write tasks
        f.write("\nTechnical Tasks:\n")
        tasks = workflow_state.get('technical_tasks', []) if isinstance(workflow_state, dict) else workflow_state.technical_tasks
        for task in tasks:
            if isinstance(task, dict):
                f.write(f"- {task.get('id', 'unknown')}: {task.get('title', 'unknown')}\n")
            else:
                f.write(f"- {task.id}: {task.title}\n")
        
        # Write code snippets
        f.write("\nCode Snippets:\n")
        snippets = workflow_state.get('code_snippets', []) if isinstance(workflow_state, dict) else workflow_state.code_snippets
        for snippet in snippets:
            if isinstance(snippet, dict):
                f.write(f"- {snippet.get('id', 'unknown')}: {snippet.get('file_path', 'No file path')}\n")
            else:
                f.write(f"- {snippet.id}: {snippet.file_path or 'No file path'}\n")
        
        # Write test cases
        f.write("\nTest Cases:\n")
        tests = workflow_state.get('test_cases', []) if isinstance(workflow_state, dict) else workflow_state.test_cases
        for test in tests:
            if isinstance(test, dict):
                f.write(f"- {test.get('id', 'unknown')}: {test.get('title', 'unknown')} ({test.get('status', 'unknown')})\n")
            else:
                f.write(f"- {test.id}: {test.title} ({test.status})\n")
        
        # Write issues
        f.write("\nIssues:\n")
        issues = workflow_state.get('issues', []) if isinstance(workflow_state, dict) else workflow_state.issues
        for issue in issues:
            if isinstance(issue, dict):
                f.write(f"- {issue.get('id', 'unknown')}: {issue.get('title', 'unknown')} ({issue.get('status', 'unknown')})\n")
            else:
                f.write(f"- {issue.id}: {issue.title} ({issue.status})\n")
        
        # Write documentation
        f.write("\nDocumentation:\n")
        docs = workflow_state.get('documentation', []) if isinstance(workflow_state, dict) else workflow_state.documentation
        for doc in docs:
            if isinstance(doc, dict):
                f.write(f"- {doc.get('id', 'unknown')}: {doc.get('title', 'unknown')} ({doc.get('doc_type', 'unknown')})\n")
            else:
                f.write(f"- {doc.id}: {doc.title} ({doc.doc_type})\n")
    
    print(f"Results saved to {os.path.join(args.output, 'result.txt')}")
    
    # Save code files
    code_dir = os.path.join(args.output, "code")
    os.makedirs(code_dir, exist_ok=True)
    
    workflow_state = result.get("workflow_state", {})
    snippets = workflow_state.get('code_snippets', []) if isinstance(workflow_state, dict) else workflow_state.code_snippets
    
    for snippet in snippets:
        file_path = None
        code = None
        
        if isinstance(snippet, dict):
            file_path = snippet.get('file_path')
            code = snippet.get('code')
        else:
            file_path = snippet.file_path
            code = snippet.code
            
        if file_path:
            # Create directories if needed
            full_path = os.path.join(code_dir, file_path.lstrip("/"))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write code file
            with open(full_path, "w") as f:
                f.write(code or "")
    
    print(f"Code files saved to {code_dir}")
    
    # Save documentation files
    doc_dir = os.path.join(args.output, "docs")
    os.makedirs(doc_dir, exist_ok=True)
    
    docs = workflow_state.get('documentation', []) if isinstance(workflow_state, dict) else workflow_state.documentation
    
    for doc in docs:
        doc_id = None
        doc_type = None
        title = None
        content = None
        
        if isinstance(doc, dict):
            doc_id = doc.get('id')
            doc_type = doc.get('doc_type')
            title = doc.get('title')
            content = doc.get('content')
        else:
            doc_id = doc.id
            doc_type = doc.doc_type
            title = doc.title
            content = doc.content
            
        if doc_id:
            file_path = os.path.join(doc_dir, f"{doc_id}_{doc_type}.md")
            with open(file_path, "w") as f:
                f.write(f"# {title}\n\n")
                f.write(content or "")
    
    print(f"Documentation files saved to {doc_dir}")


if __name__ == "__main__":
    main()
