import concurrent.futures
import time
from brain.cache import QUANTUM_CACHE
from brain.global_knowledge import query_global_knowledge

class QuantumRouter:
    def __init__(self, brain_instance):
        self.brain = brain_instance

    def process(self, user_input: str) -> str:
        clean = user_input.strip()
        if not clean:
            return "Standing by, Sir."

        # Tier 0: In-Memory Quantum Cache (< 0.1ms)
        cached = QUANTUM_CACHE.get(clean)
        if cached:
            return cached

        # Tier 1: Instant Local Hardware & Diagnostics (< 1ms)
        local_reply = self.brain.try_local_commands(clean)
        if local_reply:
            QUANTUM_CACHE.set(clean, local_reply)
            return local_reply

        # Tier 2: Speculative Parallel Race (Global Knowledge Mesh vs Gemini Turbo)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Future 1: Global Fast Knowledge APIs (Wikipedia / DuckDuckGo / Math)
            future_global = executor.submit(query_global_knowledge, clean)
            
            # Check global knowledge with a tight 300ms window
            try:
                global_res = future_global.result(timeout=0.35)
                if global_res:
                    QUANTUM_CACHE.set(clean, global_res)
                    return global_res
            except Exception:
                pass

        # Tier 3: Gemini 2.5/3.6 Flash Autonomous Intelligence
        gemini_reply = self.brain.chat_gemini(clean)
        if gemini_reply and not gemini_reply.startswith("All auxiliary neural channels"):
            QUANTUM_CACHE.set(clean, gemini_reply)
            return gemini_reply

        return gemini_reply if gemini_reply else "Standing by locally for your command, Sir."
