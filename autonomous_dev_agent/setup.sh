#!/bin/bash

# Setup script for Autonomous Software Development Agent

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p output/code
mkdir -p output/docs
mkdir -p feedback_data

# Create .env file template
echo "Creating .env file template..."
cat > .env.template << EOL
# API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# GitHub/GitLab settings
GITHUB_TOKEN=your_github_token
GITHUB_USERNAME=your_github_username
GITHUB_REPO=your_github_repo

# Optional GitLab settings
GITLAB_TOKEN=your_gitlab_token
GITLAB_PROJECT_ID=your_gitlab_project_id
EOL

echo "Setup complete! Please copy .env.template to .env and add your API keys."
echo "To activate the environment, run: source venv/bin/activate"
echo "To run the agent, use: python -m src.main --requirements path/to/requirements.txt"
