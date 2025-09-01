"""
Toy LLM models for a tiny debate demo.

Each model is extremely simple: it uses templates + small randomness to produce
plausible-sounding arguments. No external API is needed.

The file intentionally aims to be beginner friendly; heavy commenting is used to
explain the design and make future modifications easier.
"""

from dataclasses import dataclass, field
from enum import Enum
import random
import textwrap
from typing import List, Optional


class Stance(str, Enum):
    """Enum of possible positions a model can take in the debate."""

    PRO = "pro"
    CON = "con"
    NEUTRAL = "neutral"


@dataclass
class SimpleLLM:
    """Minimalistic language model used by the debate engine.

    Attributes:
        name: Name displayed when the model speaks.
        tone: Short descriptor inserted into templates (e.g., "passionate").
        persuasion: 0..1 value representing how persuasive the model tries to be.
        seed: Optional random seed so outputs can be made reproducible. Each model
            gets its own independent pseudo random generator.
    """

    name: str
    tone: str
    persuasion: float
    seed: Optional[int] = None
    # ``seed_state`` is created after initialization because ``random.Random``
    # cannot be represented directly as a dataclass default.
    seed_state: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # Clamp persuasion to the valid range and create an RNG using the seed.
        self.persuasion = max(0.0, min(1.0, self.persuasion))
        self.seed_state = random.Random(self.seed)

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------
    @property
    def stance(self) -> Stance:
        """The position taken by this model (subclasses override)."""

        return Stance.NEUTRAL

    def _pick(self, options: List[str]) -> str:
        """Helper to deterministically pick from a list using the model RNG."""

        return self.seed_state.choice(options)

    def generate(self, topic: str, context: Optional[str] = None) -> str:
        """Produce a short argument for ``topic``.

        Args:
            topic: Subject under debate.
            context: Previous utterance, which allows a model to reference or
                summarize prior content.

        Returns:
            A formatted string containing the model's statement.
        """

        # Simple templates provide varied yet deterministic phrasing.
        opening = self._pick([
            "I believe",
            "It's clear to me",
            "From my point of view",
            "Consider that",
        ])

        stance_phrase = self._stance_phrase(topic, context)
        reasons = self._reasons(topic, context)

        closing = self._pick([
            "That's why I'm convinced.",
            "This is the heart of the matter.",
            "In short, the evidence points there.",
            "Ultimately, the conclusion follows.",
        ])

        output = f"{opening} {stance_phrase} {reasons} {closing}"
        # ``textwrap.fill`` wraps the string nicely for terminal output.
        return textwrap.fill(output, width=80)

    # The following methods are intentionally left abstract. Subclasses provide
    # concrete implementations tailored to their perspective.
    def _stance_phrase(self, topic: str, context: Optional[str]) -> str:
        raise NotImplementedError

    def _reasons(self, topic: str, context: Optional[str]) -> str:
        raise NotImplementedError


class Proponent(SimpleLLM):
    @property
    def stance(self) -> Stance:
        return Stance.PRO

    def _stance_phrase(self, topic, context):
        return f"we should support {topic}"

    def _reasons(self, topic, context):
        candidates = [
            f"{topic} would unlock new opportunities and drive innovation.",
            f"{topic} addresses urgent challenges and creates long-term value.",
            f"{topic} empowers people and expands our options."
        ]
        reason = self._pick(candidates)
        modifier = self._pick([
            "Moreover,",
            "Importantly,",
            "Significantly,"
        ])
        confidence = self._confidence_word()
        return f"{modifier} {reason} {confidence}"

    def _confidence_word(self):
        if self.persuasion > 0.75:
            return "This is undeniable."
        if self.persuasion > 0.4:
            return "This is convincing."
        return "This seems plausible."


class Opponent(SimpleLLM):
    @property
    def stance(self) -> Stance:
        return Stance.CON

    def _stance_phrase(self, topic, context):
        return f"we should be cautious about {topic}"

    def _reasons(self, topic, context):
        candidates = [
            f"{topic} carries risks that could be overlooked.",
            f"{topic} might create unintended negative consequences.",
            f"{topic} could be costly and favor the wrong actors."
        ]
        reason = self._pick(candidates)
        modifier = self._pick([
            "However,",
            "On the other hand,",
            "Yet,"
        ])
        caution = self._caution_word()
        return f"{modifier} {reason} {caution}"

    def _caution_word(self):
        if self.persuasion > 0.75:
            return "We must not rush in."
        if self.persuasion > 0.4:
            return "We should investigate further."
        return "We should proceed carefully."


class Moderator(SimpleLLM):
    @property
    def stance(self) -> Stance:
        return Stance.NEUTRAL

    def _stance_phrase(self, topic, context):
        # Moderator summarizes or reframes; avoid taking the same pro/con stance.
        if context:
            # Provide a short summary of the last message without endorsing.
            summary = context[:140].rstrip('.')
            return f"I'll summarize: {summary}"
        return f"let's examine {topic} from several angles"

    def _reasons(self, topic, context):
        candidates = [
            "The pros and cons deserve clear comparison.",
            "Key trade-offs need to be weighed transparently.",
            "We should ask who benefits and who bears the cost."
        ]
        reason = self._pick(candidates)
        suggestion = self._pick([
            "A pilot program might help.",
            "Clear metrics could guide decisions.",
            "Stakeholder input is essential."
        ])
        return f"{reason} {suggestion}"