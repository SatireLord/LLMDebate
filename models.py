"""
LLM models for debate demo.

Supports both toy template-based models and real AI models via Ollama.
For real AI models, Ollama must be installed and running locally.
"""
import random
import textwrap
import json
import sys
from typing import Optional, Dict, Any

# Try to import Ollama client, fall back gracefully if not available
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None

class BaseLLM:
    """Base class for all LLM models in the debate system."""
    
    def __init__(self, name: str, tone: str, persuasion: float, seed: Optional[int] = None):
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
    def stance(self) -> str:
        """One of: 'pro', 'con', 'neutral' — override in subclasses."""
        return "neutral"

    def generate(self, topic: str, context: Optional[str] = None) -> str:
        """
        Produce an argument for the given topic.
        context: previous message or None
        Returns a string.
        """
        raise NotImplementedError


class SimpleLLM(BaseLLM):
    """Template-based toy model for simple debates."""

    def _pick(self, options):
        return self.seed_state.choice(options)

    def generate(self, topic: str, context: Optional[str] = None) -> str:
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
    def stance(self):
        return "con"

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
    def stance(self):
        return "neutral"

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


class OllamaLLM(BaseLLM):
    """Real AI model using Ollama for local inference."""
    
    def __init__(self, name: str, tone: str, persuasion: float, model_name: str, 
                 stance_type: str = "neutral", seed: Optional[int] = None):
        """
        model_name: str - Ollama model name (e.g., 'llama3', 'mistral', 'phi3')
        stance_type: str - 'pro', 'con', or 'neutral'
        """
        super().__init__(name, tone, persuasion, seed)
        self.model_name = model_name
        self.stance_type = stance_type
        
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama library not available. Install with: pip install ollama")
        
        # Test if Ollama is running and model is available
        try:
            ollama.list()
        except Exception as e:
            print(f"Warning: Could not connect to Ollama. Make sure Ollama is running.")
            print(f"Error: {e}")
    
    @property
    def stance(self) -> str:
        return self.stance_type
    
    def generate(self, topic: str, context: Optional[str] = None) -> str:
        """Generate response using Ollama model."""
        try:
            # Craft the prompt based on stance and context
            prompt = self._create_prompt(topic, context)
            
            # Generate response using Ollama
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'max_tokens': 200,
                    'top_p': 0.9
                }
            )
            
            text = response['response'].strip()
            
            # Clean and format the response
            text = self._clean_response(text)
            return textwrap.fill(text, width=80)
            
        except Exception as e:
            print(f"Error generating response with {self.model_name}: {e}")
            # Fallback to a simple response
            return f"I apologize, but I'm having technical difficulties discussing {topic}."
    
    def _create_prompt(self, topic: str, context: Optional[str] = None) -> str:
        """Create a prompt based on stance and context."""
        
        # Base personality description
        personality_map = {
            'pro': f"You are {self.name}, a {self.tone} advocate who supports ideas and looks for benefits and opportunities.",
            'con': f"You are {self.name}, a {self.tone} critic who questions ideas and points out potential risks and downsides.", 
            'neutral': f"You are {self.name}, a {self.tone} moderator who summarizes different viewpoints and seeks balanced analysis."
        }
        
        personality = personality_map.get(self.stance_type, personality_map['neutral'])
        
        # Context handling
        context_part = ""
        if context and self.stance_type == 'neutral':
            context_part = f"\n\nPrevious speaker said: \"{context[:200]}...\"\nProvide a brief, balanced summary of their point."
        elif context:
            context_part = f"\n\nPrevious speaker said: \"{context[:200]}...\"\nRespond with your perspective."
        
        # Stance-specific instructions
        if self.stance_type == 'pro':
            instruction = f"Argue in favor of: {topic}. Explain why this is beneficial and should be supported. Be persuasive but respectful. Limit your response to 2-3 sentences."
        elif self.stance_type == 'con':
            instruction = f"Argue against: {topic}. Explain the potential problems, risks, or downsides. Be skeptical but constructive. Limit your response to 2-3 sentences."
        else:  # neutral
            instruction = f"Provide a balanced perspective on: {topic}. Summarize key considerations without taking a strong position. Limit your response to 2-3 sentences."
        
        prompt = f"""{personality}

{instruction}{context_part}

Response (2-3 sentences max):"""
        
        return prompt
    
    def _clean_response(self, text: str) -> str:
        """Clean and format the AI response."""
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "As an AI", "I believe", "In my opinion", "I think", 
            "Response:", "Answer:", "Here's my perspective:"
        ]
        
        for prefix in prefixes_to_remove:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
                break
        
        # Ensure it doesn't start with punctuation
        if text and text[0] in ',.!?;:':
            text = text[1:].strip()
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        return text


# Enhanced model factory functions
def create_toy_models(seed: Optional[int] = None) -> list:
    """Create the original toy models."""
    a = Proponent(name="Argus (Pro)", tone="passionate", persuasion=0.8, seed=seed)
    b = Opponent(name="Boreas (Con)", tone="skeptical", persuasion=0.7, seed=seed and seed+1)
    c = Moderator(name="Clio (Moderator)", tone="measured", persuasion=0.5, seed=seed and seed+2)
    return [a, b, c]


def create_ai_models(seed: Optional[int] = None) -> list:
    """Create real AI models using Ollama."""
    if not OLLAMA_AVAILABLE:
        print("Warning: Ollama not available, falling back to toy models")
        return create_toy_models(seed)
    
    # Top 3 open source models
    models = [
        OllamaLLM(
            name="Llama3 (Pro)", 
            tone="confident", 
            persuasion=0.8, 
            model_name="llama3", 
            stance_type="pro", 
            seed=seed
        ),
        OllamaLLM(
            name="Mistral (Con)", 
            tone="analytical", 
            persuasion=0.7, 
            model_name="mistral", 
            stance_type="con", 
            seed=seed and seed+1
        ),
        OllamaLLM(
            name="Phi3 (Moderator)", 
            tone="balanced", 
            persuasion=0.5, 
            model_name="phi3", 
            stance_type="neutral", 
            seed=seed and seed+2
        )
    ]
    
    return models


def get_available_models() -> list:
    """Get list of available Ollama models."""
    if not OLLAMA_AVAILABLE:
        return []
    
    try:
        models = ollama.list()
        return [model['name'] for model in models.get('models', [])]
    except:
        return []