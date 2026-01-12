import os
import json
import time

SCORES_DIR = "scores"
FILES_DIR = "files"

def ensure_directories():
    os.makedirs(SCORES_DIR, exist_ok=True)
    os.makedirs(FILES_DIR, exist_ok=True)

def get_score_path(game_id: str) -> str:
    return os.path.join(SCORES_DIR, f"{game_id}.json")

def load_score(game_id: str) -> dict:
    path = get_score_path(game_id)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_score(game_id: str, data: dict):
    path = get_score_path(game_id)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def update_last_studied(game_id: str):
    data = load_score(game_id)
    data['last_studied'] = time.time()
    save_score(game_id, data)

def update_last_tested(game_id: str):
    data = load_score(game_id)
    data['last_tested'] = time.time()
    save_score(game_id, data)

def record_mistake(game_id: str, fen: str, played: str, expected: str):
    data = load_score(game_id)
    if 'mistakes' not in data:
        data['mistakes'] = []
    
    data['mistakes'].append({
        'timestamp': time.time(),
        'fen': fen,
        'played': played,
        'expected': expected,
        'resolved': False
    })
    save_score(game_id, data)

def resolve_mistake(game_id: str, fen: str, expected: str):
    data = load_score(game_id)
    if 'mistakes' in data:
        changed = False
        for m in data['mistakes']:
            if m.get('fen') == fen and m.get('expected') == expected and not m.get('resolved', False):
                m['resolved'] = True
                changed = True
        if changed:
            save_score(game_id, data)

def get_unresolved_mistakes(game_id: str) -> list:
    data = load_score(game_id)
    return [m for m in data.get('mistakes', []) if not m.get('resolved', False)]

def record_node_training(game_id: str, node_id: str):
    save_score(game_id, data)

    if 'node_stats' not in data:
        data['node_stats'] = {}
    
    if node_id not in data['node_stats']:
        data['node_stats'][node_id] = {}
        
    data['node_stats'][node_id]['last_trained'] = time.time()
    save_score(game_id, data)

def record_node_test(game_id: str, node_id: str, success: bool):
    data = load_score(game_id)
    if 'node_stats' not in data:
        data['node_stats'] = {}
    
    if node_id not in data['node_stats']:
        data['node_stats'][node_id] = {}
        
    data['node_stats'][node_id]['last_tested'] = time.time()
    data['node_stats'][node_id]['last_test_success'] = success
    save_score(game_id, data)