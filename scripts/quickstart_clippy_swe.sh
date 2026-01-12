#!/bin/bash
# Quick start script for Clippy SWE Agent

echo "======================================================================"
echo "CLIPPY SWE AGENT - QUICK START"
echo "======================================================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
REQUIRED_VERSION="3.10"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) and sys.version_info < (3,14) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.10-3.13 required, found: $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python version: $PYTHON_VERSION"
echo ""

# Check if OAI_CONFIG_LIST exists
echo "Checking for API configuration..."
if [ ! -f "OAI_CONFIG_LIST" ]; then
    echo "⚠️  OAI_CONFIG_LIST not found"
    echo ""
    echo "Creating sample configuration file..."
    cat > OAI_CONFIG_LIST.example << 'EOF'
[
  {
    "model": "gpt-4",
    "api_key": "your-openai-api-key-here"
  }
]
EOF
    echo "✅ Created OAI_CONFIG_LIST.example"
    echo "   Please rename to OAI_CONFIG_LIST and add your API key"
    echo ""
else
    echo "✅ OAI_CONFIG_LIST found"
    echo ""
fi

# Install dependencies
echo "======================================================================"
echo "INSTALLATION OPTIONS"
echo "======================================================================"
echo ""
echo "Choose an installation option:"
echo ""
echo "1. Basic CLI (Recommended for quick start)"
echo "   pip install -e '.[openai,mcp-proxy-gen]'"
echo ""
echo "2. Full Installation (All features)"
echo "   pip install -e '.[openai,windows-clippy-mcp,mcp-proxy-gen,browser-use]'"
echo ""
echo "3. Development Installation (For contributors)"
echo "   pip install -e '.[dev,openai,mcp-proxy-gen]'"
echo ""
read -p "Enter choice (1-3) or 's' to skip: " choice

case $choice in
    1)
        echo ""
        echo "Installing basic CLI..."
        pip install -e '.[openai,mcp-proxy-gen]'
        ;;
    2)
        echo ""
        echo "Installing full features..."
        pip install -e '.[openai,windows-clippy-mcp,mcp-proxy-gen,browser-use]'
        ;;
    3)
        echo ""
        echo "Installing development environment..."
        pip install -e '.[dev,openai,mcp-proxy-gen]'
        ;;
    s|S)
        echo "Skipping installation"
        ;;
    *)
        echo "Invalid choice, skipping installation"
        ;;
esac

echo ""
echo "======================================================================"
echo "USAGE EXAMPLES"
echo "======================================================================"
echo ""
echo "After installation, try these commands:"
echo ""
echo "1. Check status:"
echo "   clippy-swe status"
echo ""
echo "2. Execute a coding task:"
echo "   clippy-swe task 'Create a Flask REST API with authentication'"
echo ""
echo "3. Research task:"
echo "   clippy-swe task 'Research best practices for React hooks' --type research"
echo ""
echo "4. With observer mode (see agent in action):"
echo "   clippy-swe task 'Fix the bug in auth.py' --observer"
echo ""
echo "5. Windows automation (Windows only):"
echo "   clippy-swe windows 'Take a screenshot and save to Desktop'"
echo ""
echo "6. View task history:"
echo "   clippy-swe history"
echo ""
echo "7. Initialize configuration:"
echo "   clippy-swe init"
echo ""
echo "======================================================================"
echo "DOCUMENTATION"
echo "======================================================================"
echo ""
echo "📚 Comprehensive Guide: CLIPPY_SWE_AGENT_GUIDE.md"
echo "📝 Examples: examples/clippy_swe_agent_example.py"
echo "🏠 Main README: README.md"
echo ""
echo "For more information, visit:"
echo "https://github.com/dayour/Clippy-Kernel"
echo ""
echo "======================================================================"
echo "✅ QUICK START COMPLETE"
echo "======================================================================"
