import json, re
from typing import Dict, Any
from config import settings
from langchain_groq.chat_models import ChatGroq

class LLMClient:
    """
    Used for interacting with LLM client (Groq)
    - generate_story() Used to generate the story.
    - extract_entities() Used to extract properties of entities and their relationships.
    - _extract_first_json()  Used to extract only the JSON part of the string.
    """


    def __init__(self):
        provider = settings.LLM_PROVIDER.lower()

        if ChatGroq is None:
            raise RuntimeError("langchain-groq is not installed. Please install it: pip install langchain-groq")
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY not set in env for Groq provider")
        # Create two Groq LLMs: one for story, one for extraction
        self.story_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.9
        )
        self.extractor_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.0
        )


    def generate_story(self, world_context: str, player_input: str) -> str:
        prompt = (
            "The system is a Dungeon Master guiding a fantasy adventure. "
            "The system narrates the continuous sequence of the storyline to the player in a max of 120 words."
            "The system creates roadblocks for the player and ask what to do in those scenarios."
            "The system can help the player a little bit if the problem is very hard."
            "Keep prior world facts and relationships consistent. Start a new story when told to start.\n"
            f"World context:\n{world_context}\n\n"
            f"Player action:\n{player_input}\n\n"
        )
        # Use ChatGroq as chat model
        msg = self.story_llm.invoke([{"role":"user","content": prompt}])
        return msg.content.strip()


    def extract_entities(self, story_text: str) -> Dict[str, Any]:
        prompt = (
            "Extract entities and relationships from the following story excerpt. Return **strict JSON only**.\n\n"
            "Use the `attributes` field to describe the state of an entity, such as its status (alive, dead, friendly, hostile) or condition.\n\n"
            "JSON format:\n"
            '{\n'
            '  "entities": [ { "name": "Goblin", "type": "NPC", "attributes": {"status": "dead", "equipment": "rusty sword"} } ],\n'
            '  "relationships": [ { "source\": \"\", \"relation\": \"\", \"target\": \"\" } ]\n'
            '}\n\n'
            "Use types: Player, NPC, Animal, Item, Location, Event, Other.\n\n"
            f"Story:\n{story_text}\n\n"
            "Return JSON exactly (no extra text)."
        )
        msg = self.extractor_llm.invoke([{"role":"user","content": prompt}])
        raw = msg.content

        jtxt = self._extract_first_json(raw)
        if not jtxt:
            return {"entities": [], "relationships": []}
        try:
            return json.loads(jtxt)
        except Exception:
            # fallback cleanup
            cleaned = re.sub(r",\s*}", "}", jtxt)
            cleaned = re.sub(r",\s*\]", "]", cleaned)
            try:
                return json.loads(cleaned)
            except Exception:
                return {"entities": [], "relationships": []}

    def _extract_first_json(self, text: str) -> str:
        start = text.find("{")
        if start == -1:
            return ""
        stack = 0
        for i in range(start, len(text)):
            c = text[i]
            if c == "{":
                stack += 1
            elif c == "}":
                stack -= 1
                if stack == 0:
                    return text[start:i+1]
        return ""