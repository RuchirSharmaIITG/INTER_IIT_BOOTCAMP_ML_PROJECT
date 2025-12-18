from config import settings
import logging
from neo4j import GraphDatabase

log = logging.getLogger("graph_store")

class GraphStore:
    """
    Storing entities and relationships in a graph database.
    - merge_entity() used for creating new nodes
    - merge_relationship() used for creating new relationships
    - fetch_context() used for fetching context from database (universal)
    - get_context_for_entities() used for fetching context from entities
    - clear_graph() used for clearing graph for debugging purposes
    """


    def __init__(self):

        self.driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
        log.info("GraphStore: using Neo4j at %s", settings.NEO4J_URI)


    def close(self):
        self.driver.close()



    def merge_entity(self, name: str, typ: str, attributes: dict = None):
        attributes = attributes or {}


        # Sanitize attribute keys: replace spaces and hyphens with underscores
        safe_attributes = {key.replace(" ", "_").replace("-", "_"): value for key, value in attributes.items()}

        label = "".join([c for c in typ.title() if c.isalnum()]) or "Entity"

        props = ", ".join([f"n.`{k}` = ${k}" for k in safe_attributes.keys()])
        params = dict(safe_attributes)

        params["name"] = name
        query = f"MERGE (n:{label} {{name:$name}})"
        if props:
            query += " SET " + props
        with self.driver.session() as s:
            s.run(query, params)


    def merge_relationship(self, src: str, rel: str, tgt: str):

        rel_label = "".join([c for c in rel.upper() if c.isalnum() or c == "_"]) or "RELATED"
        query = (
                "MERGE (a {name:$src}) MERGE (b {name:$tgt}) "
                f"MERGE (a)-[r:{rel_label}]->(b)"
            )
        with self.driver.session() as s:
            s.run(query, {"src": src, "tgt": tgt})


    def fetch_context(self, limit: int = 100):
        """
        Return a textual summary of relationships for use in prompts.
        """

        q = """
            MATCH (a)-[r]->(b)
            RETURN labels(a)[0] AS a_type, a.name AS a_name, type(r) AS rel, labels(b)[0] AS b_type, b.name AS b_name
            LIMIT $limit
            """
        with self.driver.session() as s:
            res = s.run(q, {"limit": limit})
            rows = [rec for rec in res]
        lines = []
        for r in rows:
            a_type = r["a_type"] or "Entity"
            a_name = r["a_name"]
            rel = r["rel"]
            b_type = r["b_type"] or "Entity"
            b_name = r["b_name"]
            lines.append(f"{a_type} '{a_name}' {rel} {b_type} '{b_name}'")
        return "\n".join(lines)



    def get_context_for_entities(self, entity_names: list, limit_per_entity: int = 5):
        """
        For a given list of entity names, find all their direct relationships.
        Returns a text summary.
        """
        if not entity_names:
            return ""

        q = """
        UNWIND $names AS entity_name
        MATCH (a {name: entity_name})-[r]-(b)
        RETURN labels(a)[0] AS a_type, a.name AS a_name, type(r) AS rel, labels(b)[0] AS b_type, b.name AS b_name
        LIMIT $limit
        """
        with self.driver.session() as s:
            # We need to run this per entity to respect the limit for each one
            lines = []
            for name in entity_names:
                params = {"names": [name], "limit": limit_per_entity}
                res = s.run(q, params)
                for r in res:
                    a_type = r["a_type"] or "Entity"
                    a_name = r["a_name"]
                    rel = r["rel"]
                    b_type = r["b_type"] or "Entity"
                    b_name = r["b_name"]
                    lines.append(f"{a_type} '{a_name}' {rel} {b_type} '{b_name}'")

        # Remove duplicates while preserving order
        return "\n".join(list(dict.fromkeys(lines)))

    def clear_graph(self):
        """Deletes all nodes and relationships from the graph. For debugging."""
        query = "MATCH (n) DETACH DELETE n"
        with self.driver.session() as s:
            s.run(query)
        log.info("Graph database has been cleared.")