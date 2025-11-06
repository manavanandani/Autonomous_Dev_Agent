# Autonomous Dev Agent# Autonomous Software Development Agent



🤖 **AI-powered development with 5-phase workflow**## Project Overview



## OverviewThe Autonomous Software Development Agent is an AI-powered system that can autonomously plan, code, debug, and document software features based on natural language requirements. It combines the latest advances in code generation with agentic decision-making to create a comprehensive development pipeline.

A streamlined autonomous development agent that helps you generate code through a structured 5-phase process:

## Architecture

- 🧠 **Planning** - Creates pseudocode and development plan

- 💻 **Code** - Generates clean, working Python code  The system is built using a multi-agent architecture with specialized agents for different parts of the software development process:

- 🧪 **Test** - Coming soon

- 🐛 **Debug** - Coming soon1. **Planning Agent**: Analyzes natural language requirements and breaks them down into technical tasks

- 📚 **Document** - Generates comprehensive documentation2. **Coding Agent**: Generates code based on technical tasks and performs code reviews

3. **Testing Agent**: Creates and executes tests for code validation

## Quick Start4. **Debugging Agent**: Identifies and fixes issues in the code

5. **Documentation Agent**: Creates technical and user documentation

### Local Development

```bashThese agents are orchestrated through a workflow system built with LangChain and LangGraph, which manages the state transitions and data flow between agents.

# Clone the repository

git clone <repository-url>## Key Features

cd autonomous-dev-agent-main-2

- **Natural Language Requirement Processing**: Convert user requirements in natural language to actionable technical tasks

# Install dependencies- **Autonomous Code Generation**: Generate high-quality code based on technical specifications

pip install -r requirements_deploy.txt- **Automated Testing**: Create and run tests to validate code functionality

- **Intelligent Debugging**: Identify and fix issues in the code

# Set environment variable for demo mode- **Comprehensive Documentation**: Generate both technical and user documentation

export DRY_RUN=true- **Version Control Integration**: Connect with GitHub/GitLab for automated PR creation

- **Interactive Learning**: Improve over time based on user feedback

# Run the application

streamlit run autonomous_dev_agent/src/ui/main_app.py## Technology Stack

```

- **Framework**: LangChain + LangGraph for workflow orchestration

### Docker Deployment- **LLM Integration**: OpenAI (default) with support for Anthropic and other providers

```bash- **Programming Languages**: Python (core system)

# Build the image- **Version Control**: GitHub and GitLab API integration

docker build -t autonomous-dev-agent .- **Configuration**: Environment variables and Pydantic settings



# Run the container## Installation

docker run -p 8501:8501 autonomous-dev-agent

```### Prerequisites



### Streamlit Cloud Deployment- Python 3.10 or higher

1. Push your code to GitHub- Git

2. Connect to Streamlit Cloud- OpenAI API key (required)

3. Set environment variable: `DRY_RUN = true`- GitHub/GitLab account (optional, for version control integration)

4. Deploy!

### Setup

## Features

- ✅ **Simple Interface** - Clean, intuitive UI1. Clone the repository:

- ✅ **Phase Visualization** - Visual progress tracking   ```bash

- ✅ **Code Generation** - AI-powered code creation   git clone https://github.com/manavanandani/Autonomous_Dev_Agent.git

- ✅ **Documentation** - Automatic documentation generation   cd Autonomous_Dev_Agent

- ✅ **Download Options** - Export code and docs   ```

- 🚧 **Testing & Debugging** - Coming in future versions

2. Create a virtual environment:

## Usage Example   ```bash

1. Enter: "write a code to add 2 numbers"   python -m venv venv

2. Watch the Planning Agent create pseudocode   source venv/bin/activate  # On Windows: venv\Scripts\activate

3. See the Code Agent generate implementation   ```

4. Get comprehensive documentation

5. Download your complete solution3. Install dependencies:

   ```bash

## Tech Stack   pip install -r requirements.txt

- **Frontend**: Streamlit   ```

- **Backend**: Python, Pydantic

- **AI**: LangChain (with DRY_RUN mode for demo)4. Create a `.env` file with your OpenAI key (required):

- **Deployment**: Docker, Streamlit Cloud   ```

   OPENAI_API_KEY=your_openai_api_key

## Environment Variables   # Optional VCS

- `DRY_RUN=true` - Enables demo mode without API keys   GITHUB_TOKEN=your_github_token

   GITHUB_USERNAME=your_github_username

---   GITHUB_REPO=your_github_repo

Made with ❤️ by the Autonomous Dev Agent Team   ```

## Usage

### Basic Usage

Run the agent from the repo root with a requirements file:

```bash
python -m autonomous_dev_agent.src.main --requirements path/to/requirements.txt --output output_directory
```

Or provide requirements interactively:

```bash
python -m autonomous_dev_agent.src.main --output output_directory
```

To simulate without external calls (no LLM/VCS), enable dry-run:

```bash
python -m autonomous_dev_agent.src.main --requirements path/to/requirements.txt --output output_directory --dry-run
```

### Version Control Integration

To use with GitHub:

```bash
python -m autonomous_dev_agent.src.main --requirements path/to/requirements.txt --output output_directory --vcs github
```

To use with GitLab:

```bash
python -m autonomous_dev_agent.src.main --requirements path/to/requirements.txt --output output_directory --vcs gitlab
```

## UI

Launch the Streamlit dashboard to submit requirements and visualize agent steps:

```bash
streamlit run autonomous_dev_agent/src/ui/app.py
```

## Project Structure

```
autonomous_dev_agent/
├── src/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── planning_agent.py
│   │   ├── coding_agent.py
│   │   ├── testing_agent.py
│   │   ├── debugging_agent.py
│   │   └── documentation_agent.py
│   ├── config/
│   │   └── config.py
│   ├── models/
│   │   └── base_models.py
│   ├── utils/
│   │   ├── llm_utils.py
│   │   ├── version_control.py
│   │   └── interactive_learning.py
│   ├── workflows/
│   │   └── development_workflow.py
│   ├── ui/
│   │   └── app.py
│   └── main.py
├── tests/
├── .github/workflows/
├── requirements.txt
├── pyproject.toml
├── Makefile
└── README.md
```

## Components

### Agents

#### Planning Agent

The Planning Agent analyzes natural language requirements and breaks them down into technical tasks. It uses LLMs to:

1. Extract specific requirements from natural language descriptions
2. Assign priorities and dependencies to requirements
3. Create detailed technical tasks for implementation

#### Coding Agent

The Coding Agent generates code based on technical tasks. It can:

1. Generate code snippets for specific tasks
2. Review code for quality and correctness
3. Improve code based on review feedback

#### Testing Agent

The Testing Agent creates and executes tests for code validation. It can:

1. Generate test cases for code snippets
2. Execute tests and collect results
3. Analyze test failures

#### Debugging Agent

The Debugging Agent identifies and fixes issues in code. It can:

1. Analyze test failures to identify issues
2. Generate fixes for identified issues
3. Verify that fixes resolve the issues

#### Documentation Agent

The Documentation Agent creates documentation for code and features. It can:

1. Generate technical documentation for code
2. Create user documentation for features
3. Generate API documentation

### Workflow Orchestration

The system uses LangGraph to orchestrate the workflow between agents. The workflow:

1. Starts with the Planning Agent to analyze requirements
2. Passes technical tasks to the Coding Agent
3. Sends code to the Testing Agent for validation
4. Routes to the Debugging Agent if tests fail
5. Sends code to the Documentation Agent for documentation
6. Optionally integrates with version control systems

### Interactive Learning

The system includes an interactive learning mechanism that:

1. Collects user feedback on agent outputs
2. Analyzes feedback to identify strengths and weaknesses
3. Generates learning points for improvement
4. Applies learning to improve agent prompts and behavior

## Development

### Adding a New Agent

To add a new agent to the system:

1. Create a new agent class that inherits from `BaseAgent`
2. Implement the `process` method to handle inputs and produce outputs
3. Add the agent to the workflow in `create_development_workflow`

### Customizing Prompts

Agent prompts can be customized by modifying the templates in each agent's initialization methods.

### Adding Version Control Providers

To add support for a new version control provider:

1. Create a new client class in `version_control.py`
2. Implement the required methods for repository operations
3. Update the `VersionControlManager` to support the new provider

## Research Connection

This project implements concepts from the February 2025 paper "CODESIM: Multi-Agent Code Generation and Problem Solving through Simulation-Driven Planning and Debugging," which achieved state-of-the-art results in program synthesis by integrating planning, coding, and debugging with human-like verification approaches.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI and Anthropic for their powerful language models
- The LangChain and LangGraph teams for their excellent frameworks
- The research community for advancing the field of AI-assisted software development
