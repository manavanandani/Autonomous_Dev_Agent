import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from autonomous_dev_agent.src.models.base_models import WorkflowState

def test_workflow_state_defaults():
	ws = WorkflowState(workflow_id="t1", current_step="init")
	assert ws.requirements == []
	assert ws.technical_tasks == []
	assert ws.code_snippets == []
	assert ws.agent_states == {}
