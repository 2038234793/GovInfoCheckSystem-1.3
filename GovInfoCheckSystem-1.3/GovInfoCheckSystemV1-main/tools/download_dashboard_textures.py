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
plugin_static_dir = os.path.join(base_dir, 'app', 'plugins', 'data_dashboard', 'static')
assets_dir = os.path.join(plugin_static_dir, 'assets')

# Ensure assets directory exists
os.makedirs(assets_dir, exist_ok=True)

# Texture files for 3D Earth
files = [
    {
        'url': 'https://raw.githubusercontent.com/apache/echarts-gl/master/test/asset/world.topo.bathy.200401.jpg',
        'path': os.path.join(assets_dir, 'world.topo.bathy.200401.jpg')
    },
    {
        'url': 'https://raw.githubusercontent.com/apache/echarts-gl/master/test/asset/starfield.jpg',
        'path': os.path.join(assets_dir, 'starfield.jpg')
    },
    {
        'url': 'https://raw.githubusercontent.com/apache/echarts-gl/master/test/asset/pisa.hdr',
        'path': os.path.join(assets_dir, 'pisa.hdr')
    }
]

# Alternative URLs if github raw is blocked (using echarts official examples or mirrors)
# Since github raw often has connectivity issues in China, let's try to use a mirror or CDN if possible,
# or just rely on the user's environment. For this script, we'll use standard URLs.

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for file_info in files:
    download_file(file_info['url'], file_info['path'])
