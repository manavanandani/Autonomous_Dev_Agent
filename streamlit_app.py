"""
Enhanced Autonomous Dev Agent - 5 Phase Structure
Phases: Planning → Code → Test → Debug → Document
"""
import streamlit as st
import asyncio
import os
import sys

# Enable DRY_RUN mode for demo
os.environ['DRY_RUN'] = 'true'

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from autonomous_dev_agent.src.agents.planning_agent import PlanningAgent
    from autonomous_dev_agent.src.agents.coding_agent import CodingAgent
    from autonomous_dev_agent.src.agents.documentation_agent import DocumentationAgent
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="🤖 Autonomous Dev Agent - Enhanced",
    page_icon="🤖",
    layout="centered"
)

# Custom CSS for enhanced design
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f4e79;
        margin-bottom: 2rem;
    }
    .phase-progress {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 0 1rem;
    }
    .phase-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        flex: 1;
    }
    .phase-step:not(:last-child)::after {
        content: '';
        position: absolute;
        top: 20px;
        right: -50%;
        width: 100%;
        height: 2px;
        background: #dee2e6;
        z-index: 0;
    }
    .phase-step.completed::after {
        background: #28a745;
    }
    .phase-step.active::after {
        background: #007bff;
    }
    .phase-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 8px;
        z-index: 1;
        position: relative;
    }
    .phase-circle.pending {
        background: #dee2e6;
        color: #6c757d;
    }
    .phase-circle.active {
        background: #007bff;
        color: white;
        animation: pulse 2s infinite;
    }
    .phase-circle.completed {
        background: #28a745;
        color: white;
    }
    .phase-circle.coming-soon {
        background: #ffc107;
        color: #212529;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 123, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0); }
    }
    .phase-label {
        font-size: 12px;
        font-weight: 600;
        text-align: center;
    }
    .step-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
    }
    .code-output {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .pseudocode {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-family: monospace;
    }
    .documentation {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .coming-soon {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state"""
    if 'step' not in st.session_state:
        st.session_state.step = 'input'
    if 'requirement' not in st.session_state:
        st.session_state.requirement = ""
    if 'pseudocode' not in st.session_state:
        st.session_state.pseudocode = ""
    if 'final_code' not in st.session_state:
        st.session_state.final_code = ""
    if 'documentation' not in st.session_state:
        st.session_state.documentation = ""
    if 'completed_phases' not in st.session_state:
        st.session_state.completed_phases = []

def get_phase_status(phase_name):
    """Get status of a phase"""
    current_step = st.session_state.step
    completed = st.session_state.completed_phases
    
    if phase_name in completed:
        return "completed"
    elif (phase_name == "planning" and current_step == "planning") or \
         (phase_name == "coding" and current_step == "coding") or \
         (phase_name == "documentation" and current_step == "documentation"):
        return "active"
    elif phase_name in ["testing", "debugging"]:
        return "coming-soon"
    else:
        return "pending"

def render_phase_progress():
    """Render the phase progress indicator"""
    phases = [
        ("planning", "🧠", "Planning"),
        ("coding", "💻", "Code"), 
        ("testing", "🧪", "Test"),
        ("debugging", "🐛", "Debug"),
        ("documentation", "📚", "Document")
    ]
    
    # Create columns for the chain layout
    cols = st.columns([1, 0.2, 1, 0.2, 1, 0.2, 1, 0.2, 1])
    
    for i, (phase_key, emoji, label) in enumerate(phases):
        status = get_phase_status(phase_key)
        
        with cols[i * 2]:  # Use every other column for phases
            if status == "completed":
                st.markdown(f"<div style='text-align: center; padding: 10px; border-radius: 50px; background: #28a745; color: white;'>{emoji} {label} ✅</div>", unsafe_allow_html=True)
            elif status == "active":
                st.markdown(f"<div style='text-align: center; padding: 10px; border-radius: 50px; background: #007bff; color: white; animation: pulse 2s infinite;'>{emoji} {label} ⚡</div>", unsafe_allow_html=True)
            elif status == "coming-soon":
                st.markdown(f"<div style='text-align: center; padding: 10px; border-radius: 50px; background: #ffc107; color: #212529;'>{emoji} {label} 🚧</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center; padding: 10px; border-radius: 50px; background: #dee2e6; color: #6c757d;'>{emoji} {label}</div>", unsafe_allow_html=True)
        
        # Add arrow between phases (except after the last phase)
        if i < len(phases) - 1:
            with cols[i * 2 + 1]:
                st.markdown("<div style='text-align: center; padding: 15px 0; font-size: 20px;'>→</div>", unsafe_allow_html=True)

def create_simple_pseudocode(requirement: str) -> str:
    """Create simple pseudocode for the requirement (keeping existing logic)"""
    req_lower = requirement.lower()
    
    if "add" in req_lower and "number" in req_lower:
        return """
PSEUDOCODE:
1. FUNCTION add_numbers(a, b)
2.     result = a + b
3.     RETURN result
4. END FUNCTION

5. INPUT: Get two numbers from user
6. CALL add_numbers with the inputs
7. DISPLAY the result
"""
    elif "calculator" in req_lower:
        return """
PSEUDOCODE:
1. DEFINE Calculator class
2.     METHOD add(a, b): RETURN a + b
3.     METHOD subtract(a, b): RETURN a - b  
4.     METHOD multiply(a, b): RETURN a * b
5.     METHOD divide(a, b): RETURN a / b
6. END CLASS

7. CREATE calculator instance
8. PROVIDE user interface for operations
"""
    elif "fibonacci" in req_lower:
        return """
PSEUDOCODE:
1. FUNCTION fibonacci(n)
2.     IF n <= 1: RETURN n
3.     RETURN fibonacci(n-1) + fibonacci(n-2)
4. END FUNCTION

5. INPUT: Get number from user
6. CALL fibonacci function
7. DISPLAY the sequence
"""
    else:
        return f"""
PSEUDOCODE:
1. ANALYZE requirement: "{requirement}"
2. BREAK DOWN into smaller tasks
3. DEFINE main function
4. IMPLEMENT core logic
5. ADD error handling
6. TEST the solution
7. RETURN final result
"""

def generate_simple_code(requirement: str, pseudocode: str) -> str:
    """Generate simple code based on requirement (keeping existing logic)"""
    req_lower = requirement.lower()
    
    if "add" in req_lower and "number" in req_lower:
        return '''def add_numbers(a, b):
    """Add two numbers and return the result"""
    return a + b

def main():
    """Main function to add two numbers"""
    try:
        # Get input from user
        num1 = float(input("Enter first number: "))
        num2 = float(input("Enter second number: "))
        
        # Add the numbers
        result = add_numbers(num1, num2)
        
        # Display result
        print(f"The sum of {num1} and {num2} is: {result}")
        
    except ValueError:
        print("Error: Please enter valid numbers")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()'''
    
    elif "calculator" in req_lower:
        return '''class Calculator:
    """Simple calculator class"""
    
    def add(self, a, b):
        """Add two numbers"""
        return a + b
    
    def subtract(self, a, b):
        """Subtract two numbers"""
        return a - b
    
    def multiply(self, a, b):
        """Multiply two numbers"""
        return a * b
    
    def divide(self, a, b):
        """Divide two numbers"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

def main():
    """Main calculator function"""
    calc = Calculator()
    
    try:
        num1 = float(input("Enter first number: "))
        operation = input("Enter operation (+, -, *, /): ")
        num2 = float(input("Enter second number: "))
        
        if operation == '+':
            result = calc.add(num1, num2)
        elif operation == '-':
            result = calc.subtract(num1, num2)
        elif operation == '*':
            result = calc.multiply(num1, num2)
        elif operation == '/':
            result = calc.divide(num1, num2)
        else:
            print("Invalid operation")
            return
            
        print(f"Result: {result}")
        
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()'''
    
    else:
        return f'''def solve_requirement():
    """
    Solution for: {requirement}
    """
    # TODO: Implement the solution based on the requirement
    print("Implementing solution for: {requirement}")
    
    # Add your implementation here
    pass

def main():
    """Main function"""
    try:
        solve_requirement()
        print("Task completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {{e}}")

if __name__ == "__main__":
    main()'''

def generate_documentation(requirement: str, code: str) -> str:
    """Generate documentation for the code"""
    req_lower = requirement.lower()
    
    if "add" in req_lower and "number" in req_lower:
        return '''# Add Numbers Function Documentation

## Overview
This module provides a simple function to add two numbers with error handling.

## Functions

### `add_numbers(a, b)`
Adds two numbers and returns the result.

**Parameters:**
- `a` (float): First number to add
- `b` (float): Second number to add

**Returns:**
- `float`: The sum of a and b

**Example:**
```python
result = add_numbers(5, 3)
print(result)  # Output: 8
```

### `main()`
Main function that handles user input and displays results.

**Features:**
- Prompts user for two numbers
- Validates input (handles non-numeric input)
- Displays the sum with proper formatting
- Includes error handling for invalid input

## Usage
Run the script directly:
```bash
python add_numbers.py
```

## Error Handling
- `ValueError`: Raised when user enters non-numeric input
- `Exception`: General error handling for unexpected issues

## Requirements
- Python 3.6+
- No external dependencies required
'''
    
    elif "calculator" in req_lower:
        return '''# Calculator Class Documentation

## Overview
A simple calculator class that performs basic arithmetic operations.

## Class: Calculator

### Methods

#### `add(a, b)`
Adds two numbers.
- **Parameters:** a (float), b (float)
- **Returns:** float - sum of a and b

#### `subtract(a, b)`
Subtracts second number from first.
- **Parameters:** a (float), b (float)  
- **Returns:** float - difference of a and b

#### `multiply(a, b)`
Multiplies two numbers.
- **Parameters:** a (float), b (float)
- **Returns:** float - product of a and b

#### `divide(a, b)`
Divides first number by second.
- **Parameters:** a (float), b (float)
- **Returns:** float - quotient of a and b
- **Raises:** ValueError if b is zero

## Usage Example
```python
calc = Calculator()
result = calc.add(10, 5)     # Returns 15
result = calc.subtract(10, 5) # Returns 5  
result = calc.multiply(10, 5) # Returns 50
result = calc.divide(10, 5)   # Returns 2.0
```

## Error Handling
- Division by zero protection
- Input validation for numeric values
- General exception handling

## Requirements
- Python 3.6+
- No external dependencies
'''
    
    else:
        return f'''# {requirement.title()} - Documentation

## Overview
This module implements a solution for: {requirement}

## Description
Generated code provides a basic implementation framework for the specified requirement.

## Functions

### `solve_requirement()`
Main implementation function for the requirement.

### `main()`
Entry point that executes the solution with error handling.

## Usage
```python
python solution.py
```

## Features
- Basic implementation structure
- Error handling
- Modular design
- Easy to extend

## Requirements
- Python 3.6+
- Additional dependencies may be needed based on specific implementation

## Notes
This is a generated template that should be customized based on specific needs.
'''

def main():
    """Main application"""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Autonomous Dev Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">AI-powered development with 5-phase workflow</p>', unsafe_allow_html=True)
    
    # Phase Progress Indicator
    render_phase_progress()
    
    # Input Phase
    if st.session_state.step == 'input':
        st.markdown('<div class="step-header">📝 Tell me what you want to build</div>', unsafe_allow_html=True)
        
        requirement = st.text_area(
            "Enter your requirement:",
            placeholder="e.g., write a code to add 2 numbers",
            height=100,
            key="requirement_input"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Development", type="primary", use_container_width=True):
                if requirement.strip():
                    st.session_state.requirement = requirement.strip()
                    st.session_state.step = 'planning'
                    st.session_state.completed_phases = []
                    st.rerun()
                else:
                    st.error("Please enter a requirement")
    
    # Planning Phase
    elif st.session_state.step == 'planning':
        st.markdown('<div class="step-header">🧠 Planning Agent - Creating Pseudocode</div>', unsafe_allow_html=True)
        
        with st.spinner("Analyzing requirements and creating plan..."):
            pseudocode = create_simple_pseudocode(st.session_state.requirement)
            st.session_state.pseudocode = pseudocode
        
        st.success("✅ Planning completed!")
        st.markdown("### 📋 Generated Pseudocode:")
        st.markdown('<div class="pseudocode">' + pseudocode.replace('\n', '<br>') + '</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 'input'
                st.rerun()
        with col3:
            if st.button("Next: Generate Code →", type="primary", use_container_width=True):
                st.session_state.completed_phases.append('planning')
                st.session_state.step = 'coding'
                st.rerun()
    
    # Coding Phase
    elif st.session_state.step == 'coding':
        st.markdown('<div class="step-header">💻 Coding Agent - Generating Implementation</div>', unsafe_allow_html=True)
        
        with st.spinner("Writing code based on pseudocode..."):
            code = generate_simple_code(st.session_state.requirement, st.session_state.pseudocode)
            st.session_state.final_code = code
        
        st.success("✅ Code generated successfully!")
        
        st.markdown("### 📋 Generated Code:")
        st.code(code, language="python")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 'planning'
                st.rerun()
        with col2:
            if st.button("📚 Document", type="secondary", use_container_width=True):
                st.session_state.completed_phases.append('coding')
                st.session_state.step = 'documentation'
                st.rerun()
        with col3:
            if st.button("🔄 New Request", use_container_width=True):
                st.session_state.step = 'input'
                st.session_state.requirement = ""
                st.session_state.pseudocode = ""
                st.session_state.final_code = ""
                st.session_state.documentation = ""
                st.session_state.completed_phases = []
                st.rerun()
        with col4:
            st.download_button(
                "📁 Download",
                data=code,
                file_name="generated_code.py",
                mime="text/plain",
                use_container_width=True
            )
    
    # Documentation Phase  
    elif st.session_state.step == 'documentation':
        st.markdown('<div class="step-header">📚 Documentation Agent - Creating Documentation</div>', unsafe_allow_html=True)
        
        with st.spinner("Generating comprehensive documentation..."):
            documentation = generate_documentation(st.session_state.requirement, st.session_state.final_code)
            st.session_state.documentation = documentation
        
        st.success("✅ Documentation generated successfully!")
        
        st.markdown("### 📖 Generated Documentation:")
        st.markdown('<div class="documentation">' + documentation.replace('\n', '<br>') + '</div>', unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            if st.button("← Back to Code", use_container_width=True):
                st.session_state.step = 'coding'
                st.rerun()
        with col2:
            if st.button("🔄 New Request", use_container_width=True):
                st.session_state.step = 'input'
                st.session_state.requirement = ""
                st.session_state.pseudocode = ""
                st.session_state.final_code = ""
                st.session_state.documentation = ""
                st.session_state.completed_phases = []
                st.rerun()
        with col3:
            st.download_button(
                "📁 Download Code",
                data=st.session_state.final_code,
                file_name="generated_code.py",
                mime="text/plain",
                use_container_width=True
            )
        with col4:
            st.download_button(
                "📄 Download Docs",
                data=documentation,
                file_name="documentation.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    # Coming Soon Phases (Test & Debug)
    if st.session_state.step in ['testing', 'debugging']:
        phase_name = "Testing" if st.session_state.step == 'testing' else "Debugging"
        emoji = "🧪" if st.session_state.step == 'testing' else "🐛"
        
        st.markdown(f'<div class="step-header">{emoji} {phase_name} Agent - Coming Soon</div>', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="coming-soon">
            <h3>🚧 {phase_name} Phase - Under Development</h3>
            <p>This phase will be available in a future version!</p>
            <p><strong>Planned Features:</strong></p>
            <ul style="text-align: left; display: inline-block;">
                {"<li>Automated unit test generation</li><li>Test case execution</li><li>Coverage analysis</li>" if st.session_state.step == 'testing' else "<li>Code analysis and bug detection</li><li>Performance optimization suggestions</li><li>Error handling improvements</li>"}
            </ul>
        </div>
        ''', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("← Back to Available Phases", type="primary", use_container_width=True):
                st.session_state.step = 'coding'
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown('<p style="text-align: center; color: #999; font-size: 0.8rem;">🤖 Enhanced Autonomous Dev Agent v2.0</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()