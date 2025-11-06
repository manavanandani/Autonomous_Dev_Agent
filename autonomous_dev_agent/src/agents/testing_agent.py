"""
Testing agent for creating and running tests for code validation.
"""
from typing import Dict, Any, List, Optional
import uuid
import os
import tempfile
import subprocess

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from autonomous_dev_agent.src.agents.base_agent import BaseAgent
from autonomous_dev_agent.src.models.base_models import CodeSnippet, TestCase
from autonomous_dev_agent.src.utils.llm_utils import get_openai_llm, create_structured_output_chain, create_text_output_chain
from autonomous_dev_agent.src.config.config import settings


class TestGenerationOutput(BaseModel):
    """
    Output schema for test generation.
    """
    test_cases: List[Dict[str, Any]] = Field(
        description="List of generated test cases for the code"
    )


class TestExecutionResult(BaseModel):
    """
    Output schema for test execution results.
    """
    test_id: str = Field(
        description="ID of the test case"
    )
    passed: bool = Field(
        description="Whether the test passed"
    )
    output: str = Field(
        description="Output from test execution"
    )
    error_message: Optional[str] = Field(
        description="Error message if the test failed",
        default=None
    )


class TestingAgent(BaseAgent):
    """
    Agent responsible for creating and running tests for code validation.
    """
    
    def __init__(self, agent_id: str = "testing_agent"):
        """
        Initialize the testing agent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        super().__init__(agent_id, "testing")
        self.llm = get_openai_llm(model=settings.TESTING_LLM_MODEL)
        
        # Initialize chains
        self._init_test_generation_chain()
        self._init_test_analysis_chain()
    
    def _init_test_generation_chain(self):
        """
        Initialize the chain for generating tests.
        """
        template = """
        You are an expert software tester. Your task is to create comprehensive test cases
        for the following code:
        
        ```{language}
        {code}
        ```
        
        Code description: {description}
        
        For each test case:
        1. Assign a unique ID
        2. Write a clear, descriptive title
        3. Provide a detailed description of what the test is checking
        4. Write the actual test code in the same language as the code being tested
        5. Specify the expected result
        
        Consider different test scenarios including:
        - Normal/happy path cases
        - Edge cases
        - Error cases
        - Performance considerations (if applicable)
        
        Return the test cases in a structured format.
        """
        
        self.test_generation_chain = create_structured_output_chain(
            self.llm,
            template,
            TestGenerationOutput
        )
    
    def _init_test_analysis_chain(self):
        """
        Initialize the chain for analyzing test results.
        """
        template = """
        You are an expert software tester. Your task is to analyze the following test results
        and provide insights:
        
        Test case: {test_case}
        
        Execution result:
        {execution_result}
        
        Please analyze the test results and provide:
        1. A summary of what passed and what failed
        2. Potential reasons for failures
        3. Recommendations for fixing the issues
        
        Be specific and technical in your analysis.
        """
        
        self.test_analysis_chain = create_text_output_chain(
            self.llm,
            template
        )
    
    def generate_tests(self, code_snippet: CodeSnippet) -> List[TestCase]:
        """
        Generate test cases for a code snippet.
        
        Args:
            code_snippet: Code snippet to generate tests for
            
        Returns:
            List of generated test cases
        """
        result = self.test_generation_chain.invoke({
            "language": code_snippet.language,
            "code": code_snippet.code,
            "description": code_snippet.description
        })
        
        test_cases = []
        
        for test_data in result.test_cases:
            # Ensure the test has an ID
            if "id" not in test_data:
                test_data["id"] = f"TEST-{uuid.uuid4().hex[:8]}"
                
            # Ensure code_snippet_ids is set
            if "code_snippet_ids" not in test_data:
                test_data["code_snippet_ids"] = [code_snippet.id]
            
            test_case = TestCase(**test_data)
            test_cases.append(test_case)
        
        return test_cases
    
    def execute_test(self, test_case: TestCase, code_snippets: List[CodeSnippet]) -> TestExecutionResult:
        """
        Execute a test case against the provided code snippets.
        
        Args:
            test_case: Test case to execute
            code_snippets: Code snippets to test
            
        Returns:
            Test execution result
        """
        # Short-circuit in dry-run mode
        if settings.DRY_RUN:
            return TestExecutionResult(
                test_id=test_case.id,
                passed=True,
                output="DRY_RUN",
                error_message=None
            )

        # Determine the language of the test
        language = None
        for code_id in test_case.code_snippet_ids:
            for snippet in code_snippets:
                if snippet.id == code_id:
                    language = snippet.language
                    break
            if language:
                break
        
        if not language:
            return TestExecutionResult(
                test_id=test_case.id,
                passed=False,
                output="",
                error_message="Could not determine language for test execution"
            )
        
        # Create temporary files for code and test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write code files
            code_files = []
            for snippet in code_snippets:
                if snippet.id in test_case.code_snippet_ids:
                    file_path = os.path.join(temp_dir, os.path.basename(snippet.file_path or f"code_{snippet.id}.{self._get_file_extension(snippet.language)}"))
                    with open(file_path, 'w') as f:
                        f.write(snippet.code)
                    code_files.append(file_path)
            
            # Write test file
            test_file = os.path.join(temp_dir, f"test_{test_case.id}.{self._get_file_extension(language)}")
            with open(test_file, 'w') as f:
                f.write(test_case.test_code)
            
            # Execute test based on language
            try:
                result = self._execute_test_by_language(language, test_file, code_files, temp_dir)
                return TestExecutionResult(
                    test_id=test_case.id,
                    passed=result["passed"],
                    output=result["output"],
                    error_message=result.get("error_message")
                )
            except Exception as e:
                return TestExecutionResult(
                    test_id=test_case.id,
                    passed=False,
                    output="",
                    error_message=f"Error executing test: {str(e)}"
                )
    
    def _get_file_extension(self, language: str) -> str:
        """
        Get the file extension for a given language.
        
        Args:
            language: Programming language
            
        Returns:
            File extension
        """
        language_extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "c++": "cpp",
            "csharp": "cs",
            "c#": "cs",
            "go": "go",
            "ruby": "rb",
            "php": "php",
            "swift": "swift",
            "kotlin": "kt",
            "rust": "rs"
        }
        
        return language_extensions.get(language.lower(), "txt")
    
    def _execute_test_by_language(self, language: str, test_file: str, code_files: List[str], working_dir: str) -> Dict[str, Any]:
        """
        Execute a test file based on the programming language.
        
        Args:
            language: Programming language
            test_file: Path to the test file
            code_files: Paths to the code files
            working_dir: Working directory for execution
            
        Returns:
            Dictionary with execution results
        """
        language = language.lower()
        
        if language == "python":
            # For Python, use pytest or unittest
            try:
                # Try to run with pytest first
                result = subprocess.run(
                    ["python", "-m", "pytest", test_file, "-v"],
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                passed = result.returncode == 0
                output = result.stdout
                error = result.stderr if result.returncode != 0 else None
            except subprocess.TimeoutExpired:
                passed = False
                output = "Test execution timed out"
                error = "Execution took longer than 30 seconds"
            except Exception as e:
                # Fall back to direct execution
                try:
                    result = subprocess.run(
                        ["python", test_file],
                        cwd=working_dir,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    passed = result.returncode == 0
                    output = result.stdout
                    error = result.stderr if result.returncode != 0 else None
                except Exception as e2:
                    passed = False
                    output = f"Failed to execute test: {str(e2)}"
                    error = str(e2)
        
        elif language in ["javascript", "typescript"]:
            # For JavaScript/TypeScript, use Node.js
            try:
                result = subprocess.run(
                    ["node", test_file],
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                passed = result.returncode == 0
                output = result.stdout
                error = result.stderr if result.returncode != 0 else None
            except Exception as e:
                passed = False
                output = f"Failed to execute test: {str(e)}"
                error = str(e)
        
        else:
            # For other languages, return a message that execution is not supported
            passed = False
            output = f"Test execution for {language} is not directly supported"
            error = "Unsupported language for direct execution"
        
        return {
            "passed": passed,
            "output": output,
            "error_message": error
        }
    
    def analyze_test_results(self, test_case: TestCase, execution_result: TestExecutionResult) -> str:
        """
        Analyze test execution results.
        
        Args:
            test_case: Test case that was executed
            execution_result: Results of the test execution
            
        Returns:
            Analysis of the test results
        """
        test_case_str = (
            f"ID: {test_case.id}\n"
            f"Title: {test_case.title}\n"
            f"Description: {test_case.description}\n"
            f"Expected Result: {test_case.expected_result}"
        )
        
        execution_result_str = (
            f"Passed: {execution_result.passed}\n"
            f"Output: {execution_result.output}\n"
            f"Error Message: {execution_result.error_message or 'None'}"
        )
        
        analysis = self.test_analysis_chain.invoke({
            "test_case": test_case_str,
            "execution_result": execution_result_str
        })
        
        return analysis
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inputs and return outputs.
        
        Args:
            inputs: Input data for the agent to process
                - code_snippet: Code snippet to generate tests for
                - code_snippets: List of code snippets to test
                - test_case: Test case to execute
                - workflow_state: Current workflow state
                
        Returns:
            Output data from the agent including:
                - test_cases: List of generated test cases
                - test_results: List of test execution results
                - test_analysis: Analysis of test results
                - workflow_state: Updated workflow state
        """
        # Update agent state
        self.update_state(status="working")
        
        # Get workflow state
        workflow_state = inputs.get("workflow_state", {})
        
        # Process based on inputs
        if "code_snippet" in inputs and inputs.get("action") == "generate_tests":
            # Generate tests for a single code snippet
            code_snippet = inputs["code_snippet"]
            if isinstance(code_snippet, dict):
                code_snippet = CodeSnippet(**code_snippet)
                
            test_cases = self.generate_tests(code_snippet)
            
            # Update workflow state
            if workflow_state:
                workflow_state.test_cases.extend(test_cases)
                workflow_state.current_step = "test_generation"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "test_cases": test_cases,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif "code_snippets" in inputs and inputs.get("action") == "generate_tests":
            # Generate tests for multiple code snippets
            code_snippets = inputs["code_snippets"]
            if isinstance(code_snippets[0], dict):
                code_snippets = [CodeSnippet(**snippet) for snippet in code_snippets]
                
            all_test_cases = []
            for snippet in code_snippets:
                test_cases = self.generate_tests(snippet)
                all_test_cases.extend(test_cases)
            
            # Update workflow state
            if workflow_state:
                workflow_state.test_cases.extend(all_test_cases)
                workflow_state.current_step = "test_generation"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "test_cases": all_test_cases,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif "test_case" in inputs and "code_snippets" in inputs and inputs.get("action") == "execute_test":
            # Execute a single test case
            test_case = inputs["test_case"]
            if isinstance(test_case, dict):
                test_case = TestCase(**test_case)
                
            code_snippets = inputs["code_snippets"]
            if isinstance(code_snippets[0], dict):
                code_snippets = [CodeSnippet(**snippet) for snippet in code_snippets]
                
            test_result = self.execute_test(test_case, code_snippets)
            
            # Update workflow state
            if workflow_state:
                # Update test case status
                for i, tc in enumerate(workflow_state.test_cases):
                    if tc.id == test_case.id:
                        workflow_state.test_cases[i].status = "passed" if test_result.passed else "failed"
                        break
                
                workflow_state.current_step = "test_execution"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "test_result": test_result,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed",
                "tests_passed": test_result.passed
            }
            
        elif "test_cases" in inputs and "code_snippets" in inputs and inputs.get("action") == "execute_tests":
            # Execute multiple test cases
            test_cases = inputs["test_cases"]
            if isinstance(test_cases[0], dict):
                test_cases = [TestCase(**tc) for tc in test_cases]
                
            code_snippets = inputs["code_snippets"]
            if isinstance(code_snippets[0], dict):
                code_snippets = [CodeSnippet(**snippet) for snippet in code_snippets]
                
            test_results = []
            all_passed = True
            
            for test_case in test_cases:
                test_result = self.execute_test(test_case, code_snippets)
                test_results.append(test_result)
                
                if not test_result.passed:
                    all_passed = False
                
                # Update test case status in workflow state
                if workflow_state:
                    for i, tc in enumerate(workflow_state.test_cases):
                        if tc.id == test_case.id:
                            workflow_state.test_cases[i].status = "passed" if test_result.passed else "failed"
                            break
            
            # Update workflow state
            if workflow_state:
                workflow_state.current_step = "test_execution"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "test_results": test_results,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed",
                "tests_passed": all_passed
            }
            
        elif "test_case" in inputs and "test_result" in inputs and inputs.get("action") == "analyze":
            # Analyze test results
            test_case = inputs["test_case"]
            if isinstance(test_case, dict):
                test_case = TestCase(**test_case)
                
            test_result = inputs["test_result"]
            if isinstance(test_result, dict):
                test_result = TestExecutionResult(**test_result)
                
            analysis = self.analyze_test_results(test_case, test_result)
            
            # Update workflow state
            if workflow_state:
                workflow_state.current_step = "test_analysis"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "test_analysis": analysis,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        else:
            # Invalid input
            self.update_state(status="error")
            return {
                "error": "Invalid input. Expected 'code_snippet'/'code_snippets' with action 'generate_tests', 'test_case'/'test_cases' with action 'execute_test'/'execute_tests', or 'test_case' and 'test_result' with action 'analyze'.",
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "error"
            }
