def remember_fact(topic: str, fact: str, category: str = "general") -> dict:
    from brain.memory import remember_fact as _rem
    return _rem(topic, fact, category)

def recall_memory(topic: str) -> dict:
    from brain.memory import recall_memory as _rec
    return _rec(topic)

def forget_memory(topic: str) -> dict:
    from brain.memory import forget_memory as _forg
    return _forg(topic)
