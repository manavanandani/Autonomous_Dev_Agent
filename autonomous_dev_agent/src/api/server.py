from typing import Optional
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import the existing workflow function
try:
    from autonomous_dev_agent.src.main import process_requirements
except Exception as e:
    # If import fails, raise during startup so user sees the error
    raise


class ProcessRequest(BaseModel):
    requirement: str
    workflow_id: Optional[str] = "api-run"
    dry_run: Optional[bool] = True
    output_dir: Optional[str] = "output"
    vcs: Optional[str] = "none"


app = FastAPI(title="Autonomous Dev Agent API")


@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "message": "Autonomous Dev Agent API is running"}


@app.post("/process", tags=["workflow"])
async def process(req: ProcessRequest):
    """Run the development workflow for the provided natural-language requirement.

    Returns the result produced by `process_requirements`.
    """
    if not req.requirement:
        raise HTTPException(status_code=400, detail="requirement is required")

    # Respect dry_run via environment setting and settings module used by the project
    if req.dry_run:
        os.environ["DRY_RUN"] = "true"
        try:
            from autonomous_dev_agent.src.config.config import settings
            settings.DRY_RUN = True
        except Exception:
            # if settings cannot be adjusted, continue and let the workflow run in best-effort dry mode
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

    # Call the project's existing function
    try:
        result = process_requirements(req.requirement, workflow_id=req.workflow_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {e}")

    # Optionally save to output/result.txt similar to CLI
    try:
        with open(os.path.join(req.output_dir, "result_api.json"), "w") as f:
            import json
            json.dump(result, f, default=lambda o: getattr(o, 'dict', lambda: str(o))(), indent=2)
    except Exception:
        # Non-fatal if saving fails
        pass

    return result
