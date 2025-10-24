import os
import sys
import json
import streamlit as st

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from autonomous_dev_agent.src.main import process_requirements

st.set_page_config(page_title="Autonomous Dev Agent", layout="wide")

st.title("Autonomous Dev Agent")

with st.sidebar:
	st.header("Settings")
	workflow_id = st.text_input("Workflow ID", value="ui-run")
	dry_run = st.toggle("Dry Run (no external calls)", value=True)
	output_dir = st.text_input("Output Directory", value="output")
	vcs = st.selectbox("Version Control", options=["none", "github", "gitlab"], index=0)
	st.divider()
	st.write("OPENAI_API_KEY set:" , bool(os.getenv("OPENAI_API_KEY")))

requirement = st.text_area("Requirement (natural language)", height=200, placeholder="As a user, I want ... so that ...")

if st.button("Run"):
	if dry_run:
		os.environ["DRY_RUN"] = "true"
		# Import and update settings to ensure dry-run is active
		from autonomous_dev_agent.src.config.config import settings
		settings.DRY_RUN = True
	else:
		os.environ["DRY_RUN"] = "false"
		from autonomous_dev_agent.src.config.config import settings
		settings.DRY_RUN = False
		
	os.makedirs(output_dir, exist_ok=True)
	with st.spinner("Running workflow..."):
		result = process_requirements(requirement, workflow_id)
	st.success("Workflow completed")
	
	# Display the generated code prominently
	ws = result.get("workflow_state", {})
	code_snippets = ws.get('code_snippets', []) if isinstance(ws, dict) else ws.code_snippets
	
	if code_snippets:
		st.subheader("🎉 Generated Code")
		for snippet in code_snippets:
			if isinstance(snippet, dict):
				file_path = snippet.get('file_path', 'unknown')
				code = snippet.get('code', '')
				language = snippet.get('language', 'python')
			else:
				file_path = snippet.file_path or 'unknown'
				code = snippet.code
				language = snippet.language
			
			st.write(f"**File:** `{file_path}`")
			st.code(code, language=language)
	else:
		st.warning("No code was generated. Check the workflow status below.")
	
	# Show workflow summary
	st.subheader("📊 Workflow Summary")
	col1, col2, col3 = st.columns(3)
	
	with col1:
		st.metric("Requirements", len(ws.get('requirements', []) if isinstance(ws, dict) else ws.requirements))
	with col2:
		st.metric("Tasks", len(ws.get('technical_tasks', []) if isinstance(ws, dict) else ws.technical_tasks))
	with col3:
		st.metric("Code Files", len(ws.get('code_snippets', []) if isinstance(ws, dict) else ws.code_snippets))
	
	# Show workflow details in an expandable section
	with st.expander("🔍 Detailed Workflow Data", expanded=False):
		st.code(json.dumps(result, default=lambda o: getattr(o, "dict", lambda: str(o))(), indent=2))
