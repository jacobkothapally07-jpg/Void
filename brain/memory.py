import os
import json
import time

MEMORY_FILE = os.path.expanduser('~/.gemini/antigravity/scratch/jarvis/memory_vault.json')

DEFAULT_PROFILE = {
    "name": {
        "fact": "Jacob Kothapally",
        "category": "profile",
        "date": "2026-08-29 00:00:00"
    },
    "organization": {
        "fact": "JK Industries",
        "category": "profile",
        "date": "2026-08-29 00:00:00"
    },
    "home location": {
        "fact": "Hyderabad, Telangana, India",
        "category": "profile",
        "date": "2026-08-29 00:00:00"
    },
    "my favorite supercar": {
        "fact": "the Aston Martin Valkyrie",
        "category": "preference",
        "date": "2026-08-29 23:01:05"
    }
}

def _load_vault() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Ensure base profile is preserved
                    for k, v in DEFAULT_PROFILE.items():
                        if k not in data:
                            data[k] = v
                    return data
        except Exception:
            return DEFAULT_PROFILE.copy()
    return DEFAULT_PROFILE.copy()

def _save_vault(vault: dict):
    try:
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, 'w') as f:
            json.dump(vault, f, indent=2)
    except Exception as e:
        print('Error saving memory vault:', e)

def remember_fact(topic: str, fact: str, category: str = "general") -> dict:
    vault = _load_vault()
    clean_topic = topic.strip().lower()
    clean_fact = fact.strip()
    
    vault[clean_topic] = {
        'fact': clean_fact,
        'category': category.lower(),
        'timestamp': time.time(),
        'date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    _save_vault(vault)
    return {
        'status': 'success',
        'topic': clean_topic,
        'fact': clean_fact,
        'category': category,
        'detail': f"Logged into your neural memory vault, Sir: {clean_topic} is {clean_fact}."
    }

def recall_memory(topic: str) -> dict:
    vault = _load_vault()
    clean_topic = topic.strip().lower()
    
    # Exact match
    if clean_topic in vault:
        return {'status': 'success', 'found': True, 'topic': clean_topic, 'fact': vault[clean_topic]['fact']}
        
    # Partial search
    for k, v in vault.items():
        if k in clean_topic or clean_topic in k:
            return {'status': 'success', 'found': True, 'topic': k, 'fact': v['fact']}
            
    return {'status': 'success', 'found': False, 'message': f'No stored memory found for "{topic}".'}

def forget_memory(topic: str) -> dict:
    vault = _load_vault()
    clean_topic = topic.strip().lower()
    
    matched_key = None
    if clean_topic in vault:
        matched_key = clean_topic
    else:
        for k in vault.keys():
            if clean_topic in k or k in clean_topic:
                matched_key = k
                break
                
    if matched_key:
        removed_fact = vault.pop(matched_key)
        _save_vault(vault)
        return {
            'status': 'success',
            'deleted': True,
            'topic': matched_key,
            'detail': f'Memory purged from neural vault: {matched_key}.'
        }
    return {
        'status': 'success',
        'deleted': False,
        'message': f'No memory matching "{topic}" was found to delete.'
    }

def get_user_profile() -> dict:
    vault = _load_vault()
    return vault

def get_all_memories_summary() -> str:
    vault = _load_vault()
    if not vault:
        return ""
    lines = ["[PERSONAL USER PROFILE & NEURAL MEMORY VAULT]"]
    lines.append("You know the following confirmed personal facts and preferences about your creator, Jacob:")
    for k, v in vault.items():
        cat = f"[{v.get('category', 'general').upper()}]"
        lines.append(f"• {cat} {k.title()}: {v['fact']}")
    return "\n".join(lines)
