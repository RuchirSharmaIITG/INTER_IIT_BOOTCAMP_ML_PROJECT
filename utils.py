def pretty_print_memory(mem):
    print("=== Graph facts ===")
    print(mem.get("graph") or "(no facts)")
    print("\n=== Episodic hits ===")
    for i, e in enumerate(mem.get("episodic", []), 1):
        text = e.get("text") or e.get("page_content") or ""
        print(f"{i}. [{e.get('score'):.4f}] {text[:300]}")
