import os
import json
import time

MEMORY_FILE = '/Users/jacobkothapally/.gemini/antigravity/scratch/jarvis/memory_vault.json'

def _load_vault() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_vault(vault: dict):
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(vault, f, indent=2)
    except Exception as e:
        print('Error saving memory vault:', e)

def remember_fact(topic: str, fact: str) -> dict:
    vault = _load_vault()
    clean_topic = topic.strip().lower()
    clean_fact = fact.strip()
    
    vault[clean_topic] = {
        'fact': clean_fact,
        'timestamp': time.time(),
        'date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    _save_vault(vault)
    return {
        'status': 'success',
        'topic': clean_topic,
        'fact': clean_fact,
        'detail': f'Memory logged in neural vault: {clean_topic} -> {clean_fact}.'
    }

def recall_memory(topic: str) -> dict:
    vault = _load_vault()
    clean_topic = topic.strip().lower()
    
    # Exact match
    if clean_topic in vault:
        return {'status': 'success', 'found': True, 'fact': vault[clean_topic]['fact']}
        
    # Partial search
    for k, v in vault.items():
        if k in clean_topic or clean_topic in k:
            return {'status': 'success', 'found': True, 'topic': k, 'fact': v['fact']}
            
    return {'status': 'success', 'found': False, 'message': f'No stored memory found for {topic}.'}

def get_all_memories_summary() -> str:
    vault = _load_vault()
    if not vault:
        return ""
    lines = ["[USER MEMORY VAULT - PREFERENCES & FACTS]"]
    for k, v in vault.items():
        lines.append(f"- {k}: {v['fact']}")
    return "\n".join(lines)
