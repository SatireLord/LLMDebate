#!/usr/bin/env python3
"""
CLI to run a debate between three LLMs with adversarial turn selection.

Supports both toy template-based models and real AI models via Ollama.

Usage:
    python debate.py "Should we colonize Mars?" --turns 6 --seed 123
    python debate.py "AI regulation?" --ai --turns 4  # Use real AI models
"""
import argparse
import sys
import random
from typing import Optional
from models import create_toy_models, create_ai_models, get_available_models, OLLAMA_AVAILABLE

def make_models(use_ai: bool = False, seed: Optional[int] = None) -> list:
    """Create models based on the specified type."""
    if use_ai:
        print("Creating AI models using Ollama...")
        if not OLLAMA_AVAILABLE:
            print("Warning: Ollama not available. Install with: pip install ollama")
            print("Falling back to toy models.")
            return create_toy_models(seed)
        
        available = get_available_models()
        required_models = ['llama3', 'mistral', 'phi3']
        missing = [m for m in required_models if not any(m in avail for avail in available)]
        
        if missing:
            print(f"Warning: Missing models {missing}. You can install them with:")
            for model in missing:
                print(f"  ollama pull {model}")
            print("Falling back to toy models for now.")
            return create_toy_models(seed)
        
        return create_ai_models(seed)
    else:
        print("Creating toy template-based models...")
        return create_toy_models(seed)

def _models_by_stance(models, stance):
    return [ (i, m) for i, m in enumerate(models) if m.stance == stance ]

def run_debate(topic: str, turns: int = 6, seed: Optional[int] = None, use_ai: bool = False) -> None:
    """Run the debate with the specified parameters."""
    models = make_models(use_ai=use_ai, seed=seed)
    rng = random.Random(seed)

    print("="*80)
    print(f"Debate topic: {topic}")
    print(f"Model type: {'AI Models (Ollama)' if use_ai else 'Toy Models'}")
    print("="*80)
    
    # Print model information
    for i, model in enumerate(models):
        print(f"Model {i+1}: {model.name} - {model.stance}")
    print("="*80)

    # select initial speaker at random
    start_idx = rng.randrange(len(models))
    current_idx = start_idx
    last_outputs = [None] * len(models)

    # Track last non-neutral stance (pro or con) so we know what to oppose next.
    last_non_neutral_stance = None
    last_output = None

    for t in range(1, turns + 1):
        model = models[current_idx]

        # Determine context: feed previous output as context if present (helps moderator summarize)
        context = last_output

        out = model.generate(topic, context=context)
        last_outputs[current_idx] = out
        last_output = out

        print(f"\n--- Turn {t} ---")
        print(f"\n{model.name} ({model.stance}):")
        print(out)

        # update last_non_neutral_stance if current model expressed pro or con
        if model.stance in ("pro", "con"):
            last_non_neutral_stance = model.stance

        # choose next speaker index
        # If current model was 'pro' -> next must be 'con'
        # If current model was 'con' -> next must be 'pro'
        # If current model was 'neutral' -> choose randomly between pro/con
        if model.stance == "pro":
            required = "con"
        elif model.stance == "con":
            required = "pro"
        else:  # neutral
            # if we have recent non-neutral, oppose that; otherwise choose randomly
            if last_non_neutral_stance == "pro":
                required = "con"
            elif last_non_neutral_stance == "con":
                required = "pro"
            else:
                required = rng.choice(["pro", "con"])

        candidates = _models_by_stance(models, required)
        if not candidates:
            # fallback: any model other than the current one
            candidates = [ (i,m) for i,m in enumerate(models) if i != current_idx ]

        # pick one at random among candidates
        next_idx = rng.choice(candidates)[0]
        current_idx = next_idx

    print("\n" + "="*80)
    print("Debate ended.")
    print("="*80)

def main(argv):
    parser = argparse.ArgumentParser(
        description="LLM debate CLI with support for toy and real AI models",
        epilog="""
Examples:
  python debate.py "Should we use renewable energy?" --turns 4
  python debate.py "AI safety concerns?" --ai --turns 6 --seed 42
  python debate.py "Universal basic income?" --ai

Note: For AI models, Ollama must be installed and running locally.
Required models: llama3, mistral, phi3
Install with: ollama pull llama3 && ollama pull mistral && ollama pull phi3
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("topic", nargs='?', help="Topic to debate (wrap in quotes)")
    parser.add_argument("--turns", type=int, default=6, help="Number of speaker turns (default: 6)")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for reproducible runs")
    parser.add_argument("--ai", action="store_true", help="Use real AI models via Ollama instead of toy models")
    parser.add_argument("--list-models", action="store_true", help="List available Ollama models and exit")
    
    args = parser.parse_args(argv)
    
    if args.list_models:
        if not OLLAMA_AVAILABLE:
            print("Ollama library not available. Install with: pip install ollama")
            return
        
        available = get_available_models()
        if available:
            print("Available Ollama models:")
            for model in available:
                print(f"  - {model}")
        else:
            print("No Ollama models found or Ollama not running.")
            print("Install models with: ollama pull <model_name>")
        return
    
    if not args.topic:
        parser.error("Topic is required unless using --list-models")
    
    run_debate(args.topic, turns=args.turns, seed=args.seed, use_ai=args.ai)

if __name__ == "__main__":
    main(sys.argv[1:])