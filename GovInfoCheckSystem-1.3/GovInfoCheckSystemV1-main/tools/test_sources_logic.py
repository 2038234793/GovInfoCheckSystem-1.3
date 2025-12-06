import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.plugins.pachong.pachong.presets import get_preset_list

try:
    print("Testing get_preset_list()...")
    sources = []
    preset_list = get_preset_list()
    for preset in preset_list:
        sources.append({
            "key": preset['key'],
            "name": preset['name'],
            "category": preset['category'],
            "type": "plugin"
        })
    print(f"Successfully retrieved {len(sources)} sources.")
    for s in sources:
        print(f" - {s['name']} ({s['category']})")
except Exception as e:
    print(f"Error: {e}")
