PYTHON=python3
PACKAGE=autonomous_dev_agent

setup:
	$(PYTHON) -m venv venv
	. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

run:
	. venv/bin/activate && $(PYTHON) -m $(PACKAGE).src.main --output output

run-dry:
	. venv/bin/activate && $(PYTHON) -m $(PACKAGE).src.main --output output --dry-run

ui:
	. venv/bin/activate && streamlit run $(PACKAGE)/src/ui/app.py

test:
	. venv/bin/activate && pytest -q --maxfail=1 --disable-warnings

lint:
	. venv/bin/activate && ruff check .

type:
	. venv/bin/activate && mypy $(PACKAGE)

rag.ingest:
	. venv/bin/activate && $(PYTHON) -m $(PACKAGE).src.rag.ingest --input docs --collection devagent

