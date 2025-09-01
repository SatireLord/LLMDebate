```markdown
# LLMDebate — 3 Super Simple LLMs That Debate Each Other

This small demo runs a debate between three toy "LLM" models (no external APIs required).
Each model is a lightweight, template-driven generator with different personalities:
Proponent (pro), Opponent (con), and Moderator (neutral).

New behavior:
- The user supplies the topic (first input).
- A starting AI is chosen at random.
- On each subsequent turn the next speaker is chosen so their stance is adversarial to
  the previous non-neutral stance (so no two consecutive responses share the same opinion).
- If the previous speaker was neutral (Moderator), the next speaker is chosen randomly to be
  pro or con.
- If multiple eligible models could speak, the selection is random.
- Moderator remains neutral: it summarizes or reframes rather than taking a pro/con stance.

How to run
1. Make sure you have Python 3.8+ installed.
2. Run the CLI:
   python debate.py "Should we colonize Mars?" --turns 6

Options
- --turns N   : total number of speaker turns (default 6)
- --seed S    : optional integer seed for deterministic randomness (useful for reproducible runs)

Example:
   $ python debate.py "Universal basic income?" --turns 5 --seed 42

Notes
- The models here are intentionally tiny and deterministic with small randomness to vary wording.
- You can extend models.py to wrap real LLM APIs (OpenAI, local models) if you want real generation.
```