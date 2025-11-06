"""
Debugging agent for identifying and fixing issues in code.
"""
from typing import Dict, Any, List, Optional
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from autonomous_dev_agent.src.agents.base_agent import BaseAgent
from autonomous_dev_agent.src.models.base_models import CodeSnippet, TestCase, Issue, TestExecutionResult
from autonomous_dev_agent.src.utils.llm_utils import get_openai_llm, create_structured_output_chain, create_text_output_chain
from autonomous_dev_agent.src.config.config import settings


class IssueIdentificationOutput(BaseModel):
    """
    Output schema for issue identification.
    """
    issues: List[Dict[str, Any]] = Field(
        description="List of identified issues in the code"
    )


class BugFixOutput(BaseModel):
    """
    Output schema for bug fixing.
    """
    fixed_code: str = Field(
        description="Fixed code with issues resolved"
    )
    changes_made: List[str] = Field(
        description="List of changes made to fix the issues"
    )
    confidence: float = Field(
        description="Confidence level in the fix (0.0 to 1.0)"
    )


class DebuggingAgent(BaseAgent):
    """
    Agent responsible for identifying and fixing issues in code.
    """
    
    def __init__(self, agent_id: str = "debugging_agent"):
        """
        Initialize the debugging agent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        super().__init__(agent_id, "debugging")
        self.llm = get_openai_llm(model=settings.DEBUGGING_LLM_MODEL)
        
        # Initialize chains
        self._init_issue_identification_chain()
        self._init_bug_fix_chain()
        self._init_fix_verification_chain()
    
    def _init_issue_identification_chain(self):
        """
        Initialize the chain for identifying issues in code.
        """
        template = """
        You are an expert software debugger. Your task is to identify issues in the following code
        based on test failures and other information:
        
        Code:
        ```{language}
        {code}
        ```
        
        Test failures:
        {test_failures}
        
        Additional context:
        {context}
        
        For each issue:
        1. Assign a unique ID
        2. Write a clear, descriptive title
        3. Provide a detailed description of the issue
        4. Identify the code snippet IDs affected
        5. Assign a severity (high, medium, low)
        
        Consider different types of issues including:
        - Logical errors
        - Syntax errors
        - Performance issues
        - Security vulnerabilities
        - Edge cases not handled
        - Incorrect assumptions
        
        Return the identified issues in a structured format.
        """
        
        self.issue_identification_chain = create_structured_output_chain(
            self.llm,
            template,
            IssueIdentificationOutput
        )
    
    def _init_bug_fix_chain(self):
        """
        Initialize the chain for fixing bugs in code.
        """
        template = """
        You are an expert software debugger. Your task is to fix the following issues in the code:
        
        Original code:
        ```{language}
        {code}
        ```
        
        Issues to fix:
        {issues}
        
        Test failures:
        {test_failures}
        
        Additional context:
        {context}
        
        Please provide:
        1. The fixed code that resolves the issues
        2. A list of specific changes made to fix each issue
        3. Your confidence level in the fix (0.0 to 1.0)
        
        Ensure your fixes address all the identified issues while maintaining the original functionality.
        """
        
        self.bug_fix_chain = create_structured_output_chain(
            self.llm,
            template,
            BugFixOutput
        )
    
    def _init_fix_verification_chain(self):
        """
        Initialize the chain for verifying bug fixes.
        """
        template = """
        You are an expert software reviewer. Your task is to verify if the following bug fix
        properly addresses the identified issues:
        
        Original code:
        ```{language}
        {original_code}
        ```
        
        Fixed code:
        ```{language}
        {fixed_code}
        ```
        
        Issues that needed to be fixed:
        {issues}
        
        Changes made:
        {changes_made}
        
        Please analyze the fix and provide:
        1. Whether the fix properly addresses each issue
        2. Any potential new issues introduced by the fix
        3. Suggestions for further improvements
        
        Be thorough and critical in your analysis.
        """
        
        self.fix_verification_chain = create_text_output_chain(
            self.llm,
            template
        )
    
    def identify_issues(self, code_snippet: CodeSnippet, test_failures: List[Dict[str, Any]], context: str = "") -> List[Issue]:
        """
        Identify issues in code based on test failures.
        
        Args:
            code_snippet: Code snippet to identify issues in
            test_failures: List of test failure information
            context: Additional context for issue identification
            
        Returns:
            List of identified issues
        """
        # Format test failures for the prompt
        test_failures_str = ""
        for failure in test_failures:
            test_case = failure.get("test_case", {})
            result = failure.get("result", {})
            
            test_failures_str += f"Test: {test_case.get('title', 'Unknown test')}\n"
            test_failures_str += f"Description: {test_case.get('description', '')}\n"
            test_failures_str += f"Expected: {test_case.get('expected_result', '')}\n"
            test_failures_str += f"Actual: {result.get('output', '')}\n"
            test_failures_str += f"Error: {result.get('error_message', '')}\n\n"
        
        result = self.issue_identification_chain.invoke({
            "language": code_snippet.language,
            "code": code_snippet.code,
            "test_failures": test_failures_str,
            "context": context
        })
        
        issues = []
        
        for issue_data in result.issues:
            # Ensure the issue has an ID
            if "id" not in issue_data:
                issue_data["id"] = f"ISSUE-{uuid.uuid4().hex[:8]}"
                
            # Ensure code_snippet_ids is set
            if "code_snippet_ids" not in issue_data:
                issue_data["code_snippet_ids"] = [code_snippet.id]
                
            issue = Issue(**issue_data)
            issues.append(issue)
        
        return issues
    
    def fix_bugs(self, code_snippet: CodeSnippet, issues: List[Issue], test_failures: List[Dict[str, Any]], context: str = "") -> Dict[str, Any]:
        """
        Fix bugs in code based on identified issues.
        
        Args:
            code_snippet: Code snippet to fix
            issues: List of issues to fix
            test_failures: List of test failure information
            context: Additional context for bug fixing
            
        Returns:
            Dictionary with fixed code and related information
        """
        # Format issues for the prompt
        issues_str = ""
        for issue in issues:
            issues_str += f"ID: {issue.id}\n"
            issues_str += f"Title: {issue.title}\n"
            issues_str += f"Description: {issue.description}\n"
            issues_str += f"Severity: {issue.severity}\n\n"
        
        # Format test failures for the prompt
        test_failures_str = ""
        for failure in test_failures:
            test_case = failure.get("test_case", {})
            result = failure.get("result", {})
            
            test_failures_str += f"Test: {test_case.get('title', 'Unknown test')}\n"
            test_failures_str += f"Description: {test_case.get('description', '')}\n"
            test_failures_str += f"Expected: {test_case.get('expected_result', '')}\n"
            test_failures_str += f"Actual: {result.get('output', '')}\n"
            test_failures_str += f"Error: {result.get('error_message', '')}\n\n"
        
        result = self.bug_fix_chain.invoke({
            "language": code_snippet.language,
            "code": code_snippet.code,
            "issues": issues_str,
            "test_failures": test_failures_str,
            "context": context
        })
        
        # Create a new code snippet with the fixed code
        fixed_snippet = CodeSnippet(
            id=f"{code_snippet.id}-fixed",
            task_id=code_snippet.task_id,
            code=result.fixed_code,
            language=code_snippet.language,
            file_path=code_snippet.file_path,
            description=f"Fixed version of {code_snippet.id}"
        )
        
        return {
            "fixed_snippet": fixed_snippet,
            "changes_made": result.changes_made,
            "confidence": result.confidence
        }
    
    def verify_fix(self, original_code_snippet: CodeSnippet, fixed_code_snippet: CodeSnippet, issues: List[Issue], changes_made: List[str]) -> str:
        """
        Verify if a bug fix properly addresses the identified issues.
        
        Args:
            original_code_snippet: Original code snippet with issues
            fixed_code_snippet: Fixed code snippet
            issues: List of issues that were fixed
            changes_made: List of changes made to fix the issues
            
        Returns:
            Verification analysis
        """
        # Format issues for the prompt
        issues_str = ""
        for issue in issues:
            issues_str += f"ID: {issue.id}\n"
            issues_str += f"Title: {issue.title}\n"
            issues_str += f"Description: {issue.description}\n"
            issues_str += f"Severity: {issue.severity}\n\n"
        
        # Format changes made for the prompt
        changes_str = "\n".join([f"- {change}" for change in changes_made])
        
        verification = self.fix_verification_chain.invoke({
            "language": original_code_snippet.language,
            "original_code": original_code_snippet.code,
            "fixed_code": fixed_code_snippet.code,
            "issues": issues_str,
            "changes_made": changes_str
        })
        
        return verification
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inputs and return outputs.
        
        Args:
            inputs: Input data for the agent to process
                - code_snippet: Code snippet to debug
                - test_failures: List of test failure information
                - issues: List of identified issues
                - action: Action to perform (identify_issues, fix_bugs, verify_fix)
                - workflow_state: Current workflow state
                
        Returns:
            Output data from the agent including:
                - issues: List of identified issues
                - fixed_snippet: Fixed code snippet
                - verification: Verification analysis
                - workflow_state: Updated workflow state
        """
        # Update agent state
        self.update_state(status="working")
        
        # Get workflow state
        workflow_state = inputs.get("workflow_state", {})
        
        # Process based on inputs
        if "code_snippet" in inputs and "test_failures" in inputs and inputs.get("action") == "identify_issues":
            # Identify issues in code
            code_snippet = inputs["code_snippet"]
            if isinstance(code_snippet, dict):
                code_snippet = CodeSnippet(**code_snippet)
                
            test_failures = inputs["test_failures"]
            context = inputs.get("context", "")
            
            issues = self.identify_issues(code_snippet, test_failures, context)
            
            # Update workflow state
            if workflow_state:
                workflow_state.issues.extend(issues)
                workflow_state.current_step = "issue_identification"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "issues": issues,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif "code_snippet" in inputs and "issues" in inputs and "test_failures" in inputs and inputs.get("action") == "fix_bugs":
            # Fix bugs in code
            code_snippet = inputs["code_snippet"]
            if isinstance(code_snippet, dict):
                code_snippet = CodeSnippet(**code_snippet)
                
            issues = inputs["issues"]
            if isinstance(issues[0], dict):
                issues = [Issue(**issue) for issue in issues]
                
            test_failures = inputs["test_failures"]
            context = inputs.get("context", "")
            
            fix_result = self.fix_bugs(code_snippet, issues, test_failures, context)
            
            # Update workflow state
            if workflow_state:
                workflow_state.code_snippets.append(fix_result["fixed_snippet"])
                
                # Update issue status
                for issue_id in [issue.id for issue in issues]:
                    for i, issue in enumerate(workflow_state.issues):
                        if issue.id == issue_id:
                            workflow_state.issues[i].status = "fixed"
                            break
                
                workflow_state.current_step = "bug_fixing"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "fixed_snippet": fix_result["fixed_snippet"],
                "changes_made": fix_result["changes_made"],
                "confidence": fix_result["confidence"],
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif "original_code_snippet" in inputs and "fixed_code_snippet" in inputs and "issues" in inputs and "changes_made" in inputs and inputs.get("action") == "verify_fix":
            # Verify bug fix
            original_code_snippet = inputs["original_code_snippet"]
            if isinstance(original_code_snippet, dict):
                original_code_snippet = CodeSnippet(**original_code_snippet)
                
            fixed_code_snippet = inputs["fixed_code_snippet"]
            if isinstance(fixed_code_snippet, dict):
                fixed_code_snippet = CodeSnippet(**fixed_code_snippet)
                
            issues = inputs["issues"]
            if isinstance(issues[0], dict):
                issues = [Issue(**issue) for issue in issues]
                
            changes_made = inputs["changes_made"]
            
            verification = self.verify_fix(original_code_snippet, fixed_code_snippet, issues, changes_made)
            
            # Update workflow state
            if workflow_state:
                workflow_state.current_step = "fix_verification"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "verification": verification,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        else:
            # Invalid input
            self.update_state(status="error")
            return {
                "error": "Invalid input. Expected 'code_snippet' and 'test_failures' with action 'identify_issues', 'code_snippet', 'issues', and 'test_failures' with action 'fix_bugs', or 'original_code_snippet', 'fixed_code_snippet', 'issues', and 'changes_made' with action 'verify_fix'.",
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "error"
            }
