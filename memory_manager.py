import time
from collections import deque
from config import settings
from llm_client import LLMClient
from graph_store import GraphStore
from vector_store import EpisodicStore
import logging
log = logging.getLogger("memory_manager")

class MemoryManager:
    """
    A memory manager system.
    - get_world_context() Builds a dynamic, filtered context based on the player's input.
    - get_world_context2() Provides a general-purpose context.
    - generate_and_update() Generates and updates the memory as the game progresses.
    - query_memory() Generates a precise memory log for the /memory <query> command
    - query_memory2() Generates a general memory log for the /dump command
    """


    def __init__(self, working_capacity: int = None):
        self.capacity = working_capacity or settings.WORKING_CAPACITY
        self.working_buffer = deque(maxlen=self.capacity)
        self.llm = LLMClient()
        self.graph = GraphStore()
        self.episodic = EpisodicStore()

    def get_world_context(self, player_input: str):
        k = settings.EPISODIC_K or 3
        parts = []

        if self.working_buffer:
            parts.append("Recent actions and DM responses:")
            for e in list(self.working_buffer):
                parts.append(f"- Player: {e['player']} | DM: {e['dm']}")

        # --- Step 1: Semantic Search for Relevant Events ---
        # Use the vector store to find the most relevant past events
        candidate_hits = self.episodic.query(player_input, k=k)
        episodic_hits = [hit for hit in candidate_hits if hit['score'] >= settings.SIMILARITY_THRESHOLD]
        episodic_hits = episodic_hits[:k]
        if episodic_hits:
            parts.append("\nRecent relevant events:")
            for hit in episodic_hits:
                parts.append("- " + hit['text'].replace("\n", " "))

        # --- Step 2: Extract Key Entities from the Current Scene ---
        # Combine recent text to find key entities for the graph search
        text_to_extract_from = player_input
        if episodic_hits:
            text_to_extract_from += "\n" + "\n".join([h['text'] for h in episodic_hits])

        # Use the LLM to find what entities we should look up in the graph
        extracted = self.llm.extract_entities(text_to_extract_from)
        entity_names = [e['name'] for e in extracted.get("entities", []) if e.get('name')]
        # Always include the player character
        # NOTE: You'll need a way to know the player's name. Let's assume it's "Kael".
        player_name = "Kael"
        if player_name not in entity_names:
            entity_names.append(player_name)

        # --- Step 3: Targeted Graph Traversal ---
        # Use the new graph store method with the extracted entities
        if entity_names:
            gctx = self.graph.get_context_for_entities(entity_names, limit_per_entity=5)
            if gctx:
                parts.append("\nRelevant world facts and relationships:")
                parts.append(gctx)

        return "\n".join(parts)

    def get_world_context2(self):
        parts = []
        # recent working
        if self.working_buffer:
            parts.append("Recent actions and DM responses:")
            for e in list(self.working_buffer):
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e["ts"]))
                parts.append(f"- [{ts}] Player: {e['player']} | DM: {e['dm']}")
        # graph summary
        gctx = self.graph.fetch_context(limit=50)
        if gctx:
            parts.append("\nWorld facts and relationships:")
            parts.append(gctx)
        # episodic top few events
        # optional: show last 3 episodic events
        last_e = self.episodic.docs[-3:] if self.episodic.docs else []
        if last_e:
            parts.append("\nRecent episodic memory:")
            for d in last_e:
                parts.append("- " + (d.get("text")[:300].replace("\n"," ") if d.get("text") else ""))
        return "\n".join(parts)

    def generate_and_update(self, player_input: str):
        # 1. build context
        context = self.get_world_context(player_input)  # Pass player_input here
        # 2. generate narrative
        dm_text = self.llm.generate_story(world_context=context, player_input=player_input)
        # 3. store episodic
        self.episodic.add_event(f"Player: {player_input}\nDM: {dm_text}", metadata={"ts": time.time()})
        # 4. extract entities
        extracted = self.llm.extract_entities(dm_text)
        ents = extracted.get("entities", []) if isinstance(extracted, dict) else []
        rels = extracted.get("relationships", []) if isinstance(extracted, dict) else []
        # 5. update graph
        for ent in ents:
            name = ent.get("name")
            typ = ent.get("type", "Other")
            attrs = ent.get("attributes", {})
            if name:
                self.graph.merge_entity(name, typ, attrs)
                log.info("Merged entity: %s (%s)", name, typ)
        for r in rels:
            src = r.get("source")
            relname = r.get("relation", "RELATED")
            tgt = r.get("target")
            if src and tgt:
                self.graph.merge_relationship(src, relname, tgt)
                log.info("Merged relation: %s -%s-> %s", src, relname, tgt)
        # 6. update working buffer
        self.working_buffer.append({"ts": time.time(), "player": player_input, "dm": dm_text})
        return dm_text

    def query_memory2(self, q: str, k: int = None):
        k = k or settings.EPISODIC_K
        episodic_hits = self.episodic.query(q, k=k)
        graph_ctx = self.graph.fetch_context(limit=50)
        return {"episodic": episodic_hits, "graph": graph_ctx}

    def query_memory(self, q: str, k: int = None):
        k = k or settings.EPISODIC_K
        episodic_hits = self.episodic.query(q, k=k)

        graph_ctx = ""
        if q:  # If there IS a query, do an intelligent search
            extracted = self.llm.extract_entities(q)
            entity_names = [e['name'] for e in extracted.get("entities", []) if e.get('name')]

            if entity_names:
                graph_ctx = self.graph.get_context_for_entities(entity_names, limit_per_entity=5)

        else:  # If there is NO query (like in /dump), get the general context
            graph_ctx = self.graph.fetch_context(limit=50)

        return {"episodic": episodic_hits, "graph": graph_ctx}

    def close(self):
        try:
            self.graph.close()
        except Exception:
            pass

    def reset_memory(self):
        """Clears all memory stores."""
        self.graph.clear_graph()
        self.episodic.docs = []
        self.episodic.persist()
        self.working_buffer.clear()
        log.info("All memory stores have been reset.")


