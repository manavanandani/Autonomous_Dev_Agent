"""
Enhanced Development Workflow with Planning and Implementation Phases
"""
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from autonomous_dev_agent.src.workflows.development_workflow import DevelopmentWorkflow
from autonomous_dev_agent.src.agents.planning_agent import PlanningAgent, ExecutionPlan, PlanStep
from autonomous_dev_agent.src.agents.coding_agent import CodingAgent
from autonomous_dev_agent.src.agents.testing_agent import TestingAgent
from autonomous_dev_agent.src.agents.documentation_agent import DocumentationAgent
from autonomous_dev_agent.src.models.base_models import WorkflowState
import logging


class EnhancedDevelopmentWorkflow(DevelopmentWorkflow):
    """
    Enhanced workflow with explicit planning and implementation phases
    """
    
    def __init__(self, workflow_id: str):
        """Initialize the enhanced workflow"""
        super().__init__(workflow_id)
        self.logger = logging.getLogger(__name__)
        
        # Initialize agents
        self.planning_agent = PlanningAgent()
        self.coding_agent = CodingAgent()
        self.testing_agent = TestingAgent()  
        self.documentation_agent = DocumentationAgent()
        
        # Add agents to the workflow
        self.add_agent(self.planning_agent)
        self.add_agent(self.coding_agent)
        self.add_agent(self.testing_agent)
        self.add_agent(self.documentation_agent)
        
        # Track execution phases
        self.current_phase = "initialized"
        self.execution_plan = None
        
    async def execute_planning_phase(
        self, 
        requirement: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the planning phase to create an execution plan
        
        Args:
            requirement: Natural language requirement description
            context: Optional context information
            
        Returns:
            Dictionary containing planning phase results
        """
        try:
            self.logger.info(f"Starting planning phase for workflow: {self.workflow_id}")
            self.current_phase = "planning"
            self.workflow_state.current_step = "planning"
            self.workflow_state.status = "in_progress"
            
            # Create execution plan using planning agent
            self.execution_plan = await self.planning_agent.create_execution_plan(
                requirement=requirement,
                context=context
            )
            
            # Update workflow state
            self.workflow_state.current_step = "planning_complete"
            
            planning_result = {
                "phase": "planning",
                "status": "completed", 
                "execution_plan": self.execution_plan.dict(),
                "ready_for_implementation": True,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info("Planning phase completed successfully")
            return {
                "workflow_id": self.workflow_id,
                "requirement": requirement,
                "planning_phase": planning_result,
                "implementation_phase": None,
                "overall_status": "planning_complete"
            }
            
        except Exception as e:
            self.logger.error(f"Error in planning phase: {str(e)}")
            self.workflow_state.status = "error"
            return {
                "workflow_id": self.workflow_id,
                "error": str(e),
                "phase": "planning",
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_implementation_phase(
        self,
        execution_plan: ExecutionPlan,
        dry_run: bool = True,
        output_dir: str = "output"
    ) -> Dict[str, Any]:
        """
        Execute the implementation phase based on the execution plan
        
        Args:
            execution_plan: The approved execution plan
            dry_run: Whether to run in dry-run mode
            output_dir: Output directory for generated files
            
        Returns:
            Dictionary containing implementation phase results
        """
        try:
            self.logger.info(f"Starting implementation phase for workflow: {self.workflow_id}")
            self.current_phase = "implementation"
            self.workflow_state.current_step = "implementation"
            self.workflow_state.status = "in_progress"
            
            # Execute implementation following the plan
            implementation_result = await self._execute_planned_implementation(
                execution_plan=execution_plan,
                dry_run=dry_run,
                output_dir=output_dir
            )
            
            # Update workflow state
            self.workflow_state.current_step = "implementation_complete"
            self.workflow_state.status = "completed"
            
            result = {
                "phase": "implementation",
                "status": "completed",
                "files_generated": implementation_result.get("files_generated", []),
                "code_generated": implementation_result.get("code_generated", {}),
                "tests_generated": implementation_result.get("tests_generated", {}),
                "documentation": implementation_result.get("documentation", ""),
                "execution_summary": implementation_result.get("summary", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info("Implementation phase completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in implementation phase: {str(e)}")
            self.workflow_state.status = "error"
            return {
                "phase": "implementation",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_test_methods(self, key_functions: List[str]) -> str:
        """Generate test methods for key functions"""
        if not key_functions:
            return ""
        
        test_methods = []
        for func in key_functions:
            test_methods.append(f"    def test_{func.lower()}(self):")
            test_methods.append(f'        """Test {func} function"""')
            test_methods.append(f"        # TODO: Test {func}")
            test_methods.append("        pass")
            test_methods.append("")
        
        return "\n".join(test_methods)
    
    async def _execute_planned_implementation(
        self,
        execution_plan: ExecutionPlan,
        dry_run: bool,
        output_dir: str
    ) -> Dict[str, Any]:
        """Execute implementation following the plan steps"""
        
        results = {
            "files_generated": [],
            "code_generated": {},
            "tests_generated": {},
            "documentation": "",
            "summary": ""
        }
        
        try:
            # Process each step in the execution plan
            for step in execution_plan.steps:
                self.logger.info(f"Executing step {step.step_number}: {step.title}")
                
                # Generate code for files specified in this step
                step_results = await self._execute_plan_step(step, execution_plan, dry_run)
                
                # Merge step results
                results["files_generated"].extend(step_results.get("files_created", []))
                results["code_generated"].update(step_results.get("code_generated", {}))
                results["tests_generated"].update(step_results.get("tests_generated", {}))
                
                if step_results.get("documentation"):
                    results["documentation"] += f"\n\n## {step.title}\n{step_results['documentation']}"
            
            # Generate overall documentation
            results["documentation"] = await self._generate_project_documentation(execution_plan, results)
            
            results["summary"] = f"Completed {len(execution_plan.steps)} implementation steps successfully"
            
        except Exception as e:
            self.logger.error(f"Error during planned implementation: {str(e)}")
            results["summary"] = f"Implementation failed at step execution: {str(e)}"
            
        return results
    
    async def _execute_plan_step(
        self, 
        step: PlanStep, 
        plan: ExecutionPlan, 
        dry_run: bool
    ) -> Dict[str, Any]:
        """Execute a specific plan step"""
        
        step_results = {
            "files_created": [],
            "code_generated": {},
            "tests_generated": {},
            "documentation": ""
        }
        
        try:
            # Generate code for files to create
            for file_path in step.files_to_create:
                if dry_run:
                    # Dry run mode - generate mock code
                    code_content = self._generate_mock_code_for_file(file_path, step, plan)
                    step_results["code_generated"][file_path] = code_content
                    step_results["files_created"].append(f"[DRY RUN] {file_path}")
                else:
                    # Real implementation - would use coding agent
                    code_content = await self._generate_real_code_for_file(file_path, step, plan)
                    step_results["code_generated"][file_path] = code_content
                    step_results["files_created"].append(file_path)
            
            # Generate tests if this is a testing step
            if "test" in step.title.lower() or any("test_" in f for f in step.files_to_create):
                test_content = await self._generate_tests_for_step(step, plan, dry_run)
                step_results["tests_generated"].update(test_content)
            
            # Generate documentation for the step
            step_results["documentation"] = self._generate_step_documentation(step, plan)
            
        except Exception as e:
            self.logger.warning(f"Error executing step {step.step_number}: {str(e)}")
            step_results["files_created"].append(f"[ERROR] {step.title}: {str(e)}")
        
        return step_results
    
    def _generate_mock_code_for_file(self, file_path: str, step: PlanStep, plan: ExecutionPlan) -> str:
        """Generate mock code content for a file"""
        
        if file_path.endswith('.py'):
            # Generate function definitions
            function_defs = ""
            if step.key_functions:
                func_lines = []
                for func in step.key_functions:
                    func_lines.append(f"def {func}():")
                    func_lines.append(f'    """Mock implementation of {func}"""')
                    func_lines.append("    pass")
                    func_lines.append("")
                function_defs = "\n".join(func_lines)
            
            return f'''"""
{step.title} - {file_path}

Generated as part of: {plan.summary}
Step: {step.description}

This is a mock implementation for development/testing purposes.
"""

def main():
    """Main function for {step.title}"""
    print("Mock implementation of {step.title}")
    
    # TODO: Implement {step.description}
    pass

{function_defs}
if __name__ == "__main__":
    main()
'''
        elif file_path.endswith('.md'):
            return f'''# {step.title}

## Description
{step.description}

## Implementation Details
- Estimated time: {step.estimated_time}
- Complexity: {step.complexity_level}

## Key Functions
{chr(10).join(f"- `{func}`" for func in step.key_functions)}

## Files Created
{chr(10).join(f"- `{f}`" for f in step.files_to_create)}

*This documentation was auto-generated from the execution plan.*
'''
        else:
            return f'''# {step.title}
# Generated for: {file_path}
# Description: {step.description}
# Part of: {plan.summary}
'''
    
    async def _generate_real_code_for_file(self, file_path: str, step: PlanStep, plan: ExecutionPlan) -> str:
        """Generate real code using the coding agent"""
        try:
            # Create coding task based on the step
            coding_task = {
                "file_path": file_path,
                "description": step.description,
                "functions_needed": step.key_functions,
                "step_context": step.dict(),
                "plan_context": plan.dict()
            }
            
            # Use coding agent to generate code
            coding_result = self.coding_agent.process(coding_task)
            
            if coding_result.get("status") == "completed":
                return coding_result.get("generated_code", "# Code generation failed")
            else:
                return f"# Error generating code for {file_path}: {coding_result.get('error', 'Unknown error')}"
                
        except Exception as e:
            self.logger.error(f"Error generating real code for {file_path}: {str(e)}")
            return f"# Error generating code: {str(e)}"
    
    async def _generate_tests_for_step(self, step: PlanStep, plan: ExecutionPlan, dry_run: bool) -> Dict[str, str]:
        """Generate tests for a step"""
        tests = {}
        
        try:
            if dry_run:
                # Generate mock tests
                for file_path in step.files_to_create:
                    if file_path.startswith("test_") or "/test_" in file_path:
                        tests[file_path] = f'''"""
Test file for {step.title}
Generated from execution plan step {step.step_number}
"""
import pytest

class Test{step.title.replace(" ", "")}:
    """Test class for {step.title}"""
    
    def test_{step.title.lower().replace(" ", "_")}(self):
        """Test {step.description}"""
        # TODO: Implement test for {step.description}
        assert True  # Placeholder test
        
    # Test methods for key functions
    {self._generate_test_methods(step.key_functions)}
'''
            else:
                # Use testing agent for real test generation
                test_task = {
                    "step": step.dict(),
                    "plan": plan.dict(),
                    "files_to_test": step.files_to_create
                }
                
                test_result = self.testing_agent.process(test_task)
                if test_result.get("status") == "completed":
                    tests.update(test_result.get("generated_tests", {}))
                    
        except Exception as e:
            self.logger.warning(f"Error generating tests for step {step.step_number}: {str(e)}")
        
        return tests
    
    def _generate_step_documentation(self, step: PlanStep, plan: ExecutionPlan) -> str:
        """Generate documentation for a step"""
        return f'''### {step.title}

**Description:** {step.description}

**Estimated Time:** {step.estimated_time}

**Complexity:** {step.complexity_level}

**Files Created:**
{chr(10).join(f"- `{f}`" for f in step.files_to_create)}

**Key Functions:**
{chr(10).join(f"- `{func}`" for func in step.key_functions)}

**Dependencies:** {", ".join(map(str, step.dependencies)) if step.dependencies else "None"}
'''
    
    async def _generate_project_documentation(self, plan: ExecutionPlan, results: Dict[str, Any]) -> str:
        """Generate overall project documentation"""
        
        doc = f'''# {plan.requirement}

## Project Overview
{plan.summary}

## Architecture
{plan.architecture_overview}

## Technology Stack
{chr(10).join(f"- {tech}" for tech in plan.technology_stack)}

## Implementation Summary
- **Total Steps Completed:** {len(plan.steps)}
- **Files Generated:** {len(results["files_generated"])}
- **Estimated Implementation Time:** {plan.total_estimated_time}

## Generated Files
{chr(10).join(f"- `{f}`" for f in results["files_generated"])}

## Testing Strategy
{plan.testing_strategy}

## Success Criteria
{chr(10).join(f"- {criteria}" for criteria in plan.success_criteria)}

## Risk Assessment
{plan.risk_assessment}

---
*This documentation was automatically generated by the Autonomous Development Agent.*
'''
        
        return doc
    
    def get_execution_plan(self) -> Optional[ExecutionPlan]:
        """Get the current execution plan"""
        return self.execution_plan
    
    def get_current_phase(self) -> str:
        """Get the current execution phase"""
        return self.current_phase