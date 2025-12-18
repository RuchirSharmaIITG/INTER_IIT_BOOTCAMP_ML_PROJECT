# AI Dungeon Master with Persistent Memory

🎥 **Watch the demo video here:** [Nexus_YT_Demo](https://youtu.be/eSkkcrE1diA?si=mLNNrnBf9FUjJFm6)

An interactive, text-based RPG powered by a Large Language Model (LLM) with an advanced, multi-layered memory architecture. This project was built for the **Inter IIT Tech Meet 14.0** AI/ML Problem Statement.

It leverages a sophisticated memory system to deliver a persistent and coherent storytelling experience, overcoming the typical limitations of LLMs in maintaining long-term context.

---

### Key Features

* **Dynamic Narrative Generation:** Uses the Groq API with Llama 3.1 for fast and creative storytelling.
* **Multi-Layered Memory System:**
    * **Short-Term Memory:** A working buffer for immediate, turn-by-turn conversational context.
    * **Long-Term Episodic Memory:** A semantic vector store using `sentence-transformers` to recall relevant past events and conversations based on meaning.
    * **Long-Term Knowledge Graph:** A **Neo4j** graph database to track the factual state of the world, including characters, items, locations, and their complex relationships.
* **Intelligent Context Retrieval (RAG):** Employs a dynamic Retrieval-Augmented Generation (RAG) pipeline that combines semantic search and targeted graph traversals. This provides the LLM with a highly focused and relevant context for each turn, ensuring narrative consistency.
* **Interactive Console:** A full command-line interface with debugging tools (`/memory`, `/dump`, `/context`, `/reset`) to inspect the AI's memory and state in real-time.

---

### Tech Stack

* **Language:** Python
* **LLM Provider:** Groq (using Llama 3.1)
* **Core Libraries:** `langchain-groq`, `sentence-transformers`, `neo4j`
* **Database:** Neo4j (Graph Database)

---

### Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Neo4j:**
    * Ensure you have a running Neo4j database (local, Docker, or AuraDB).

4.  **Configure Environment Variables:**
    * Create a file named `.env` in the root directory.
    * Add your credentials to the `.env` file. Use `env.example` as a template:
        ```
        GROQ_API_KEY="your-groq-api-key"
        NEO4J_URI="your-neo4j-uri"
        NEO4J_USER="your-neo4j-username"
        NEO4J_PASSWORD="your-neo4j-password"
        WORKING_CAPACITY=6
        SIMILARITY_THRESHOLD=0.7
        EPISODIC_K=4
        ```

---

### How to Run

Execute the `main.py` script from your terminal:

```bash
python main.py
```

## 📬 Contact

- 🔗 [LinkedIn Profile](https://www.linkedin.com/in/ruchir-sharma-243a10337/)
