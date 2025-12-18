import sys, traceback
from memory_manager import MemoryManager
from utils import pretty_print_memory
import os

def repl():
    print("Summoning the Dungeon Master...")
    manager = MemoryManager()
    manager.reset_memory()
    print("I am the Dungeon Master. Type your action or '/help' for commands. You can type start to start the game!")
    if os.path.exists("episodic_store.json"):
        os.remove("episodic_store.json")
    try:

        while True:
            raw = input("\n> ").strip()
            if not raw:
                continue
            if raw.startswith("/"):
                cmd = raw[1:].strip().lower()
                if cmd in ("quit", "exit"):
                    print("Exiting.")
                    break
                elif cmd == "help":
                    print("Commands:\n /help\n /exit or /quit\n /memory <query>  -- query episodic & graph\n /context -- print current prompt context\n /dump -- print entire graph summary + episodic store")
                elif cmd.startswith("memory"):
                    parts = raw.split(" ", 1)
                    q = parts[1] if len(parts) > 1 else ""
                    mem = manager.query_memory(q or "")
                    pretty_print_memory(mem)
                elif cmd == "context":
                    ctx = manager.get_world_context2()
                    print("=== World Context ===")
                    print(ctx or "(no context)")

                elif cmd == "reset": # for debugging purposes
                    manager.reset_memory()
                    print("--- All memory has been cleared. A new story can begin. ---")

                elif cmd == "dump":
                    mem = manager.query_memory2("", k=20)
                    pretty_print_memory(mem)
                    print("\n=== Working buffer ===")
                    for e in manager.working_buffer:
                        print(f"- Player: {e['player']} | DM: {e['dm'][:300]}")
                else:
                    print("Unknown command. Type /help")
                continue

            # normal player turn
            try:
                dm = manager.generate_and_update(raw)
                print("\n--- DM ---\n")
                print(dm)
            except Exception as e:
                print("Error during generation:", e)
                traceback.print_exc()
    finally:
        manager.graph.clear_graph()
        manager.close()
        if os.path.exists("episodic_store.json"):
             os.remove("episodic_store.json")


if __name__ == "__main__":
    repl()


