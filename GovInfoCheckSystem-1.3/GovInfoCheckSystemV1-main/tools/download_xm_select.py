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
static_css_dir = os.path.join(base_dir, 'static', 'css')

# Ensure directories exist
os.makedirs(static_js_dir, exist_ok=True)
os.makedirs(static_css_dir, exist_ok=True)

# Files to download
files = [
    {
        # Using a reliable CDN (unpkg)
        'url': 'https://unpkg.com/xm-select@1.2.4/dist/xm-select.js',
        'path': os.path.join(static_js_dir, 'xm-select.js')
    }
]

for file_info in files:
    download_file(file_info['url'], file_info['path'])
