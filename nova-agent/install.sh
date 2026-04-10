#!/bin/bash
# Nova Agent installer

set -e

echo "╔╗╔╔═╗╦  ╦╔═╗"
echo "║║║║ ║╚╗╔╝╠═╣"
echo "╝╚╝╚═╝ ╚╝ ╩ ╩"
echo "AI-Powered Computer Agent"
echo ""

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 10), 'Python 3.10+ required'" 2>/dev/null || {
    echo "Error: Python 3.10+ is required"
    exit 1
}

echo "→ Installing Nova Agent..."
pip install -e . --quiet

echo "→ Creating config directory..."
mkdir -p ~/.nova

echo ""
echo "✓ Nova Agent installed successfully!"
echo ""
echo "Usage:"
echo "  nova              # Interactive mode"
echo "  nova organize .   # Organize current directory"
echo "  nova system       # System info"
echo "  nova --help       # All commands"
echo ""

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "! For AI features, set your API key:"
    echo "  export ANTHROPIC_API_KEY=your-key-here"
    echo ""
fi
