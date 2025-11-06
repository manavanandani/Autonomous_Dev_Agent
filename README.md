# Autonomous Dev Agent

🤖 **AI-powered development with 5-phase workflow**

## Overview
A streamlined autonomous development agent that helps you generate code through a structured 5-phase process:

- 🧠 **Planning** - Creates pseudocode and development plan
- 💻 **Code** - Generates clean, working Python code  
- 🧪 **Test** - Coming soon
- 🐛 **Debug** - Coming soon
- 📚 **Document** - Generates comprehensive documentation

## 🚀 Deploy Your Beautiful Interface

### Option 1: Streamlit Cloud (Recommended)
**The gorgeous interface you love** with visual phase chains, animations, and beautiful styling:

1. **Fork this repository** on GitHub
2. Go to **[Streamlit Cloud](https://share.streamlit.io/)**
3. Click **"New app"**
4. Select your forked repository  
5. Set **Main file path**: `streamlit_app.py`
6. Set **Environment variable**: `DRY_RUN = true`
7. Click **"Deploy"** ✨

**Result**: Beautiful Streamlit interface with:
- Animated phase progress chains
- Visual indicators (completed ✅, active ⚡, coming soon 🚧)
- Professional gradients and styling
- Download buttons for code and docs

### Option 2: Vercel (Simple Static)
Basic HTML version for quick static hosting:

1. Fork this repository
2. Go to **[Vercel](https://vercel.com/new)**
3. Import your repository
4. Deploy automatically (uses `index.html`)

## Local Development
```bash
# Clone the repository
git clone https://github.com/manavanandani/Autonomous_Dev_Agent.git
cd Autonomous_Dev_Agent

# Install dependencies
pip install -r requirements.txt

# Set environment variable for demo mode
export DRY_RUN=true

# Run the beautiful Streamlit interface
streamlit run streamlit_app.py
```

## Features
- ✅ **Beautiful UI** - Streamlit interface with animations and visual progress
- ✅ **Phase Visualization** - Visual progress chain with status indicators
- ✅ **Code Generation** - AI-powered code creation with heuristics
- ✅ **Documentation** - Automatic documentation generation
- ✅ **Download Options** - Export code and docs
- 🚧 **Testing & Debugging** - Coming in future versions

## Usage Example
1. Enter: "write a code to add 2 numbers"
2. Watch the Planning Agent create pseudocode (🧠 → ⚡)
3. See the Code Agent generate implementation (💻 → ✅)
4. Get comprehensive documentation (📚 → ✅)
5. Download your complete solution

## Tech Stack
- **Frontend**: Streamlit (beautiful animations & styling)
- **Backend**: Python, Pydantic
- **AI**: LangChain (with DRY_RUN mode for demo)
- **Deployment**: Streamlit Cloud (recommended) or Vercel (static)

## Environment Variables
- `DRY_RUN=true` - Enables demo mode without API keys

---
Made with ❤️ by the Autonomous Dev Agent Team