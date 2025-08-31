#!/usr/bin/env python3
"""
Demo script showcasing the difference between toy and AI models.
Run this to see how both modes work on the same topic.
"""

import subprocess
import sys

def run_demo():
    print("🎭 LLMDebate Demo - Comparing Toy vs AI Models")
    print("=" * 60)
    
    topic = "Should we invest more in renewable energy?"
    
    print("\n🎪 TOY MODELS DEMO")
    print("=" * 30)
    print("Running with simple template-based models...")
    print()
    
    # Run toy model debate
    result = subprocess.run([
        sys.executable, "debate.py", topic, 
        "--turns", "4", "--seed", "42"
    ], capture_output=False)
    
    print("\n\n🤖 AI MODELS DEMO")
    print("=" * 30)
    print("Running with real AI models (if available)...")
    print()
    
    # Run AI model debate
    result = subprocess.run([
        sys.executable, "debate.py", topic,
        "--ai", "--turns", "4", "--seed", "42"
    ], capture_output=False)
    
    print("\n\n📊 SUMMARY")
    print("=" * 20)
    print("🎪 Toy Models:")
    print("  - Fast and reliable")
    print("  - Template-based responses") 
    print("  - No external dependencies")
    print("  - Good for testing debate logic")
    print()
    print("🤖 AI Models:")
    print("  - Sophisticated reasoning")
    print("  - Natural language responses")
    print("  - Requires Ollama + model downloads")
    print("  - Better for real debates")
    print()
    print("💡 Try your own topics:")
    print('  python debate.py "Your topic here" --turns 6')
    print('  python debate.py "Your topic here" --ai --turns 6')

if __name__ == "__main__":
    run_demo()