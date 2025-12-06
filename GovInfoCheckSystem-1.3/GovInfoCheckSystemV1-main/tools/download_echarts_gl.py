import os
import requests

def download_file(url, filepath):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        print(f"Skipping {filepath} (already exists)")
        return True
        
    print(f"Downloading {url} to {filepath}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print("Success!")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

# Base directories
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_js_dir = os.path.join(base_dir, 'static', 'js')

# Download echarts-gl
url = "https://cdn.jsdelivr.net/npm/echarts-gl@2/dist/echarts-gl.min.js"
path = os.path.join(static_js_dir, 'echarts-gl.min.js')

download_file(url, path)
