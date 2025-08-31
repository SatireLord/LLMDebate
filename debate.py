#!/usr/bin/env python3
"""
Tiny CLI to run a debate between three toy LLMs with adversarial turn selection.

Usage:
    python debate.py "Should we colonize Mars?" --turns 6 --seed 123
"""
import argparse
import sys
import random
from models import Proponent, Opponent, Moderator

def make_models(seed=None):
    # Provide the same seed to all models for reproducible internal choices if desired.
    a = Proponent(name="Argus (Pro)", tone="passionate", persuasion=0.8, seed=seed)
    b = Opponent(name="Boreas (Con)", tone="skeptical", persuasion=0.7, seed=seed and seed+1)
    c = Moderator(name="Clio (Moderator)", tone="measured", persuasion=0.5, seed=seed and seed+2)
    return [a, b, c]

def _models_by_stance(models, stance):
    return [ (i, m) for i, m in enumerate(models) if m.stance == stance ]

def run_debate(topic, turns=6, seed=None):
    # Validate topic input
    if not topic or not topic.strip():
        print("Error: Please provide a non-empty topic for the debate.")
        return
    
    topic = topic.strip()
    models = make_models(seed=seed)
    rng = random.Random(seed)

    print("="*80)
    print(f"Debate topic: {topic}")
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
    parser = argparse.ArgumentParser(description="Tiny LLM debate CLI with adversarial turns")
    parser.add_argument("topic", help="Topic to debate (wrap in quotes)")
    parser.add_argument("--turns", type=int, default=6, help="Number of speaker turns")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for reproducible runs")
    args = parser.parse_args(argv)
    run_debate(args.topic, turns=args.turns, seed=args.seed)

if __name__ == "__main__":
    main(sys.argv[1:])