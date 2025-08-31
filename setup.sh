#!/bin/bash
# LLMDebate Setup Script
# Installs Ollama and required AI models for the debate system

set -e

echo "🎭 LLMDebate Setup Script"
echo "========================"

# Check if running on supported OS
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✅ Supported OS detected: $OSTYPE"
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "Please install Ollama manually from https://ollama.ai/"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo "✅ Ollama already installed"
else
    echo "🚀 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Start Ollama service in background
echo "🔧 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to start..."
sleep 5

# Download required models
echo "🧠 Downloading AI models (this may take a while)..."
echo "📥 Downloading Llama3..."
ollama pull llama3

echo "📥 Downloading Mistral..."
ollama pull mistral

echo "📥 Downloading Phi-3..."
ollama pull phi3

echo "✅ Setup complete!"
echo ""
echo "🎉 You can now run AI-powered debates:"
echo "   python debate.py \"Your topic here\" --ai"
echo ""
echo "📝 Example commands:"
echo "   python debate.py \"Should AI be regulated?\" --ai --turns 6"
echo "   python debate.py \"Climate change solutions?\" --ai"
echo ""
echo "🔍 To see available models:"
echo "   python debate.py --list-models"
echo ""
echo "💡 The Ollama service is running in the background (PID: $OLLAMA_PID)"
echo "   To stop it later, run: kill $OLLAMA_PID"