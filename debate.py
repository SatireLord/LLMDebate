#!/usr/bin/env python3
"""
Tiny CLI to run a debate between three toy LLMs with adversarial turn selection.

Usage:
    python debate.py "Should we colonize Mars?" --turns 6 --seed 123
"""
import argparse
import sys
import random
from typing import List, Optional, Tuple

from models import Moderator, Opponent, Proponent, SimpleLLM, Stance


def make_models(seed: Optional[int] = None) -> List[SimpleLLM]:
    """Instantiate the default trio of debaters.

    Supplying a seed makes all random choices reproducible which is useful for
    debugging or demonstrations. Each model gets a unique offset seed so they
    behave slightly differently while still being deterministic.
    """

    a = Proponent(name="Argus (Pro)", tone="passionate", persuasion=0.8, seed=seed)
    b = Opponent(
        name="Boreas (Con)",
        tone="skeptical",
        persuasion=0.7,
        seed=seed and seed + 1,
    )
    c = Moderator(
        name="Clio (Moderator)",
        tone="measured",
        persuasion=0.5,
        seed=seed and seed + 2,
    )
    return [a, b, c]


def _models_by_stance(models: List[SimpleLLM], stance: Stance) -> List[Tuple[int, SimpleLLM]]:
    """Return ``(index, model)`` pairs for all models that match ``stance``."""

    return [(i, m) for i, m in enumerate(models) if m.stance == stance]


def _select_next_index(
    models: List[SimpleLLM],
    current_idx: int,
    last_non_neutral: Optional[Stance],
    rng: random.Random,
) -> int:
    """Decide which model should speak next.

    The rules enforce an adversarial flow: a "pro" statement is followed by a
    "con" one and vice versa. A neutral moderator may be followed by either.
    If no model of the required stance exists, any other model is chosen.
    """

    current_model = models[current_idx]

    if current_model.stance == Stance.PRO:
        required = Stance.CON
    elif current_model.stance == Stance.CON:
        required = Stance.PRO
    else:  # current speaker is neutral
        if last_non_neutral == Stance.PRO:
            required = Stance.CON
        elif last_non_neutral == Stance.CON:
            required = Stance.PRO
        else:
            required = rng.choice([Stance.PRO, Stance.CON])

    candidates = _models_by_stance(models, required)
    if not candidates:
        # Fallback: choose any model other than the current one.
        candidates = [(i, m) for i, m in enumerate(models) if i != current_idx]

    return rng.choice(candidates)[0]


def run_debate(topic: str, turns: int = 6, seed: Optional[int] = None) -> str:
    """Run a debate for ``topic`` between the default models and return text.

    The original CLI printed results directly to ``stdout``.  Returning the
    complete transcript instead makes the function reusable by other
    interfaces, such as a GUI.  The caller can choose whether to print or store
    the output.

    Args:
        topic: The question or statement being debated.
        turns: Total number of speaker turns to execute.
        seed: Optional random seed for deterministic behavior.

    Returns:
        A single string containing the full debate transcript.
    """

    models = make_models(seed=seed)
    rng = random.Random(seed)

    # Collect output lines in a list; this avoids printing during generation
    # and allows the caller to handle the text however they wish.
    lines: List[str] = []

    lines.append("=" * 80)
    lines.append(f"Debate topic: {topic}")
    lines.append("=" * 80)

    # Select the initial speaker at random. ``current_idx`` will keep track of
    # the speaker for each turn.
    current_idx = rng.randrange(len(models))

    # ``last_non_neutral`` remembers the last pro/con stance so a moderator can
    # respond with an opposing viewpoint. ``last_output`` stores the full text of
    # the previous message so the moderator can summarize it.
    last_non_neutral: Optional[Stance] = None
    last_output: Optional[str] = None

    for t in range(1, turns + 1):
        model = models[current_idx]

        # Pass the previous output as context to allow summarization or rebuttal.
        out = model.generate(topic, context=last_output)
        last_output = out

        lines.append(f"\n--- Turn {t} ---")
        lines.append(f"\n{model.name} ({model.stance.value}):")
        lines.append(out)

        if model.stance in (Stance.PRO, Stance.CON):
            last_non_neutral = model.stance

        current_idx = _select_next_index(models, current_idx, last_non_neutral, rng)

    lines.append("\n" + "=" * 80)
    lines.append("Debate ended.")
    lines.append("=" * 80)

    # Joining with newlines recreates the readable transcript format used by the CLI
    return "\n".join(lines)

def main(argv):
    parser = argparse.ArgumentParser(description="Tiny LLM debate CLI with adversarial turns")
    parser.add_argument("topic", help="Topic to debate (wrap in quotes)")
    parser.add_argument("--turns", type=int, default=6, help="Number of speaker turns")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for reproducible runs")
    args = parser.parse_args(argv)
    # ``run_debate`` now returns the full transcript so we print it here.
    transcript = run_debate(args.topic, turns=args.turns, seed=args.seed)
    print(transcript)

if __name__ == "__main__":
    main(sys.argv[1:])