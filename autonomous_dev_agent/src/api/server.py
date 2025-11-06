from typing import Optional, Dict, Any, List
import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Enable DRY_RUN mode for demo purposes (no API keys required)
os.environ['DRY_RUN'] = 'true'

# Import the existing and new workflow functions
try:
    from autonomous_dev_agent.src.main import process_requirements
    from autonomous_dev_agent.src.workflows.enhanced_workflow import EnhancedDevelopmentWorkflow
    from autonomous_dev_agent.src.agents.planning_agent import ExecutionPlan
except Exception as e:
    # If import fails, raise during startup so user sees the error
    raise


# Request/Response Models
class ProcessRequest(BaseModel):
    requirement: str
    workflow_id: Optional[str] = "api-run"
    dry_run: Optional[bool] = True
    output_dir: Optional[str] = "output"
    vcs: Optional[str] = "none"


class PlanningRequest(BaseModel):
    requirement: str
    workflow_id: Optional[str] = "api-workflow"
    context: Optional[Dict[str, Any]] = None


class ImplementationRequest(BaseModel):
    execution_plan: Dict[str, Any]  # ExecutionPlan as dict
    workflow_id: str
    dry_run: Optional[bool] = True
    output_dir: Optional[str] = "output"


class PlanningResponse(BaseModel):
    workflow_id: str
    status: str
    execution_plan: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


class ImplementationResponse(BaseModel):
    workflow_id: str
    status: str
    files_generated: List[str] = []
    code_generated: Dict[str, str] = {}
    tests_generated: Dict[str, str] = {}
    documentation: str = ""
    execution_summary: str = ""
    error: Optional[str] = None
    timestamp: str


app = FastAPI(
    title="🤖 Autonomous Dev Agent API - Enhanced",
    description="AI-powered development agent with planning and implementation phases",
    version="2.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
async def root():
    """Health check and API information"""
    return {
        "status": "ok", 
        "message": "🤖 Enhanced Autonomous Dev Agent API is running",
        "version": "2.0.0",
        "features": [
            "🧠 AI-powered planning phase",
            "⚒️ Guided implementation phase", 
            "🔄 Multi-phase workflow",
            "📊 Detailed execution plans",
            "🧪 Dry run mode support"
        ],
        "endpoints": {
            "planning": "/planning - Create execution plans",
            "implementation": "/implementation - Execute implementation", 
            "complete_workflow": "/workflow/complete - Full workflow",
            "legacy_process": "/process - Legacy single-phase workflow"
        }
    }


@app.post("/planning", response_model=PlanningResponse, tags=["enhanced-workflow"])
async def create_execution_plan(request: PlanningRequest):
    """
    🧠 Create a detailed execution plan for the given requirement
    
    This is the first phase of the enhanced workflow where we analyze the requirement
    and create a comprehensive implementation plan with steps, timeline, and architecture.
    """
    try:
        # Create enhanced workflow
        workflow = EnhancedDevelopmentWorkflow(request.workflow_id)
        
        # Execute planning phase
        result = await workflow.execute_planning_phase(
            requirement=request.requirement,
            context=request.context
        )
        
        if result.get('overall_status') == 'planning_complete':
            return PlanningResponse(
                workflow_id=request.workflow_id,
                status="completed",
                execution_plan=result['planning_phase']['execution_plan'],
                timestamp=datetime.now().isoformat()
            )
        else:
            return PlanningResponse(
                workflow_id=request.workflow_id,
                status="failed",
                error=result.get('error', 'Unknown error during planning'),
                timestamp=datetime.now().isoformat()
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Planning phase failed: {str(e)}"
        )


@app.post("/implementation", response_model=ImplementationResponse, tags=["enhanced-workflow"])
async def execute_implementation(request: ImplementationRequest):
    """
    ⚒️ Execute the implementation phase based on an approved execution plan
    
    This is the second phase where we generate code, tests, and documentation
    following the detailed execution plan from the planning phase.
    """
    try:
        # Create enhanced workflow
        workflow = EnhancedDevelopmentWorkflow(request.workflow_id)
        
        # Convert dict back to ExecutionPlan object
        execution_plan = ExecutionPlan(**request.execution_plan)
        
        # Execute implementation phase
        result = await workflow.execute_implementation_phase(
            execution_plan=execution_plan,
            dry_run=request.dry_run,
            output_dir=request.output_dir
        )
        
        if result.get('status') == 'completed':
            return ImplementationResponse(
                workflow_id=request.workflow_id,
                status="completed",
                files_generated=result.get('files_generated', []),
                code_generated=result.get('code_generated', {}),
                tests_generated=result.get('tests_generated', {}),
                documentation=result.get('documentation', ""),
                execution_summary=result.get('execution_summary', ""),
                timestamp=datetime.now().isoformat()
            )
        else:
            return ImplementationResponse(
                workflow_id=request.workflow_id,
                status="failed",
                error=result.get('error', 'Unknown error during implementation'),
                timestamp=datetime.now().isoformat()
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Implementation phase failed: {str(e)}"
        )


@app.post("/workflow/complete", tags=["enhanced-workflow"])
async def complete_workflow(request: PlanningRequest):
    """
    🚀 Complete enhanced workflow - planning + implementation in one call
    
    For automated workflows where you want both phases to run sequentially
    without manual plan review. The execution plan will be auto-approved.
    """
    try:
        # Create enhanced workflow
        workflow = EnhancedDevelopmentWorkflow(request.workflow_id)
        
        # Phase 1: Planning
        planning_result = await workflow.execute_planning_phase(
            requirement=request.requirement,
            context=request.context
        )
        
        if planning_result.get('overall_status') != 'planning_complete':
            raise HTTPException(
                status_code=400, 
                detail=f"Planning phase failed: {planning_result.get('error', 'Unknown planning error')}"
            )
        
        # Phase 2: Implementation (auto-approve plan)
        execution_plan = ExecutionPlan(**planning_result['planning_phase']['execution_plan'])
        
        implementation_result = await workflow.execute_implementation_phase(
            execution_plan=execution_plan,
            dry_run=True,  # Default to dry run for safety
            output_dir="output"
        )
        
        return {
            "workflow_id": request.workflow_id,
            "status": "completed",
            "planning_phase": planning_result['planning_phase'],
            "implementation_phase": implementation_result,
            "timestamp": datetime.now().isoformat(),
            "message": "🎉 Complete workflow executed successfully!"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Complete workflow failed: {str(e)}"
        )


@app.get("/workflow/{workflow_id}/status", tags=["workflow-management"])
async def get_workflow_status(workflow_id: str):
    """📊 Get the status of a specific workflow"""
    # In a production implementation, you'd store workflow state in a database
    return {
        "workflow_id": workflow_id,
        "status": "This endpoint will track actual workflow status in future versions",
        "message": "Workflow status tracking with database persistence coming soon!",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/process", tags=["legacy"])
async def process(req: ProcessRequest):
    """
    🔄 Legacy single-phase workflow (maintained for backwards compatibility)
    
    This endpoint maintains compatibility with the original workflow approach.
    For new integrations, consider using the enhanced planning + implementation workflow.
    """
    if not req.requirement:
        raise HTTPException(status_code=400, detail="requirement is required")

    # Set dry run environment
    if req.dry_run:
        os.environ["DRY_RUN"] = "true"
        try:
            from autonomous_dev_agent.src.config.config import settings
            settings.DRY_RUN = True
        except Exception:
            pass
    else:
        os.environ.pop("DRY_RUN", None)
        try:
            from autonomous_dev_agent.src.config.config import settings
            settings.DRY_RUN = False
        except Exception:
            pass

    # Create output directory
    os.makedirs(req.output_dir, exist_ok=True)

    # Call the original workflow function
    try:
        result = process_requirements(req.requirement, workflow_id=req.workflow_id)
        
        # Save results
        try:
            with open(os.path.join(req.output_dir, "result_api.json"), "w") as f:
                import json
                json.dump(result, f, default=lambda o: getattr(o, 'dict', lambda: str(o))(), indent=2)
        except Exception:
            pass  # Non-fatal if saving fails

        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Legacy workflow failed: {e}")


# Health and monitoring endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "autonomous-dev-agent-api",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "planning_agent": True,
            "enhanced_workflow": True,
            "dry_run_mode": True,
            "legacy_compatibility": True
        }
    }


@app.get("/api/info", tags=["information"])
async def api_info():
    """API information and usage guide"""
    return {
        "name": "🤖 Autonomous Dev Agent API",
        "version": "2.0.0",
        "description": "AI-powered development automation with intelligent planning",
        "workflow_phases": {
            "1_planning": {
                "endpoint": "/planning",
                "description": "Analyze requirements and create detailed execution plans",
                "output": "Comprehensive implementation roadmap with steps and timeline"
            },
            "2_implementation": {
                "endpoint": "/implementation", 
                "description": "Execute code generation based on approved plan",
                "output": "Generated code files, tests, and documentation"
            },
            "complete": {
                "endpoint": "/workflow/complete",
                "description": "Run both phases automatically",
                "output": "Complete implementation with planning context"
            }
        },
        "usage_example": {
            "planning": "POST /planning with requirement description",
            "review": "Review the returned execution plan",
            "implementation": "POST /implementation with approved plan",
            "result": "Download generated code and documentation"
        },
        "benefits": [
            "🧠 Intelligent planning before coding",
            "📊 Detailed project roadmaps",
            "⚒️ Structured implementation approach", 
            "🧪 Comprehensive testing strategy",
            "📚 Auto-generated documentation",
            "🔄 Iterative plan refinement"
        ]
    }
