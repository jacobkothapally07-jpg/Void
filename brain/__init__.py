def __getattr__(name):
    if name == "JarvisBrain":
        from brain.llm_client import JarvisBrain
        return JarvisBrain
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
