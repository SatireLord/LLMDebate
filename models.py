"""
Toy LLM models for a tiny debate demo.

Each model is extremely simple: it uses templates + small randomness
to produce plausible-sounding arguments. No external API needed.
"""
import random
import textwrap

class SimpleLLM:
    def __init__(self, name, tone, persuasion, seed=None):
        """
        name: str - model name shown in the debate
        tone: str - short descriptor used in templates (e.g., "passionate")
        persuasion: float - 0..1 how strongly it tries to persuade
        seed: optional seed for randomness to make outputs reproducible
        """
        self.name = name
        self.tone = tone
        self.persuasion = max(0.0, min(1.0, persuasion))
        self.seed_state = random.Random(seed)

    @property
    def stance(self):
        """One of: 'pro', 'con', 'neutral' — override in subclasses."""
        return "neutral"

    def _pick(self, options):
        return self.seed_state.choice(options)

    def generate(self, topic, context=None):
        """
        Produce a short argument for the given topic.
        context: previous message or None
        Returns a string.
        """
        opening = self._pick([
            "I believe",
            "It's clear to me",
            "From my point of view",
            "Consider that"
        ])
        stance_phrase = self._stance_phrase(topic, context)
        reasons = self._reasons(topic, context)
        closing = self._pick([
            "That's why I'm convinced.",
            "This is the heart of the matter.",
            "In short, the evidence points there.",
            "Ultimately, the conclusion follows."
        ])
        output = f"{opening} {stance_phrase} {reasons} {closing}"
        return textwrap.fill(output, width=80)

    def _stance_phrase(self, topic, context):
        raise NotImplementedError

    def _reasons(self, topic, context):
        raise NotImplementedError


class Proponent(SimpleLLM):
    @property
    def stance(self):
        return "pro"

    def _stance_phrase(self, topic, context):
        # Create more natural pro-stance phrases
        topic_lower = topic.lower()
        if topic_lower.endswith('?'):
            # Handle questions naturally
            topic_statement = topic[:-1]  # Remove the question mark
            return f"the answer is yes - {topic_statement} is beneficial"
        else:
            return f"we should embrace {topic}"

    def _reasons(self, topic, context):
        # Use "this approach" or "this idea" instead of repeating the full topic
        # For questions, remove the question mark when used as a subject
        topic_ref = "this approach" if len(topic) > 30 else topic.rstrip('?')
        candidates = [
            f"{topic_ref} would unlock new opportunities and drive innovation.",
            f"{topic_ref} addresses urgent challenges and creates long-term value.",
            f"{topic_ref} empowers people and expands our options."
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
    def stance(self):
        return "con"

    def _stance_phrase(self, topic, context):
        # Create more natural con-stance phrases
        topic_lower = topic.lower()
        if topic_lower.endswith('?'):
            # Handle questions naturally
            topic_statement = topic[:-1]  # Remove the question mark
            return f"the answer is no - {topic_statement} poses significant risks"
        else:
            return f"we should be wary of {topic}"

    def _reasons(self, topic, context):
        # Use "this approach" or "this idea" instead of repeating the full topic
        # For questions, remove the question mark when used as a subject
        topic_ref = "this approach" if len(topic) > 30 else topic.rstrip('?')
        candidates = [
            f"{topic_ref} carries risks that could be overlooked.",
            f"{topic_ref} might create unintended negative consequences.",
            f"{topic_ref} could be costly and favor the wrong actors."
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
    def stance(self):
        return "neutral"

    def _stance_phrase(self, topic, context):
        # Moderator summarizes or reframes; avoid taking the same pro/con stance.
        if context:
            # Provide a short summary of the last message without endorsing.
            summary = context[:100].rstrip('.')
            return f"to summarize the previous point: {summary}..."
        topic_ref = "this issue" if len(topic) > 30 else topic.rstrip('?')
        return f"let's examine {topic_ref} from multiple perspectives"

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