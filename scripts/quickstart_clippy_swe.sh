#!/bin/bash
# Quick start script for Clippy SWE

echo "======================================================================"
echo "CLIPPY SWE QUICK START"
echo "======================================================================"
echo ""

echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) and sys.version_info < (3,14) else 1)" 2>/dev/null; then
    echo "ERROR: Python 3.10-3.13 required, found: $PYTHON_VERSION"
    exit 1
fi

echo "Python version: $PYTHON_VERSION"
echo ""

echo "Checking for API configuration..."
if [ ! -f "OAI_CONFIG_LIST" ]; then
    echo "WARNING: OAI_CONFIG_LIST not found in the current workspace"
    echo "Creating OAI_CONFIG_LIST.example"
    cat > OAI_CONFIG_LIST.example << 'EOF'
[
  {
    "model": "gpt-4",
    "api_key": "your-api-key"
  }
]
EOF
    echo "Created OAI_CONFIG_LIST.example"
    echo "Copy it to OAI_CONFIG_LIST or use the shared Copilot config path documented in CLIPPY_SWE_AGENT_GUIDE.md"
    echo ""
else
    echo "OAI_CONFIG_LIST found"
    echo ""
fi

echo "======================================================================"
echo "INSTALLATION OPTIONS"
echo "======================================================================"
echo ""
echo "Choose an installation option:"
echo ""
echo "1. CLI baseline"
echo "   pip install -e '.[openai,mcp-proxy-gen]'"
echo ""
echo "2. Extended local evaluation setup"
echo "   pip install -e '.[openai,anthropic,gemini,copilot-sdk,windows-clippy-mcp,mcp-proxy-gen]'"
echo ""
echo "3. Contributor setup"
echo "   pip install -e '.[dev,openai,mcp-proxy-gen]'"
echo ""
read -p "Enter choice (1-3) or 's' to skip: " choice

case $choice in
    1)
        echo ""
        echo "Installing CLI baseline..."
        pip install -e '.[openai,mcp-proxy-gen]'
        ;;
    2)
        echo ""
        echo "Installing extended local evaluation setup..."
        pip install -e '.[openai,anthropic,gemini,copilot-sdk,windows-clippy-mcp,mcp-proxy-gen]'
        ;;
    3)
        echo ""
        echo "Installing contributor setup..."
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
echo "FIRST COMMANDS"
echo "======================================================================"
echo ""
echo "After installation, try these commands:"
echo ""
echo "1. Initialize workspace config:"
echo "   clippy-swe init --workspace ."
echo ""
echo "2. Check status:"
echo "   clippy-swe status"
echo ""
echo "3. Run a safe research task:"
echo "   clippy-swe task 'Summarize the repository layout and highlight Clippy SWE entry points' --type research"
echo ""
echo "4. Start interactive mode:"
echo "   clippy-swe interactive"
echo ""
echo "5. Review recent task history:"
echo "   clippy-swe history --limit 5"
echo ""
echo "6. Optional Windows-only command:"
echo "   clippy-swe windows 'Summarize current system status and suggest what to inspect next'"
echo ""
echo "NOTE: If no usable LLM configuration is available, task execution will fail with:"
echo "      Cannot execute task without LLM configuration"
echo ""
echo "======================================================================"
echo "CANONICAL DOCUMENTATION"
echo "======================================================================"
echo ""
echo "User guide: CLIPPY_SWE_AGENT_GUIDE.md"
echo "Developer guide: CLIPPY_KERNEL_DEVELOPER_GUIDE.md"
echo "Evaluation guide: CLIPPY_SWE_EVALS.md"
echo "Quick start: QUICKSTART_SWE.md"
echo "Main README: README.md"
echo ""
echo "======================================================================"
echo "QUICK START COMPLETE"
echo "======================================================================"
