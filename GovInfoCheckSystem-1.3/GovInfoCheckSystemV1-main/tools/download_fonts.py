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
plugin_static_dir = os.path.join(base_dir, 'app', 'plugins', 'chatroom', 'static')
webfonts_dir = os.path.join(plugin_static_dir, 'webfonts')

# Font Awesome 6.4.0 fonts
base_url = "https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/webfonts"
fonts = [
    "fa-brands-400.ttf",
    "fa-brands-400.woff2",
    "fa-regular-400.ttf",
    "fa-regular-400.woff2",
    "fa-solid-900.ttf",
    "fa-solid-900.woff2",
    "fa-v4compatibility.ttf",
    "fa-v4compatibility.woff2"
]

for font in fonts:
    url = f"{base_url}/{font}"
    path = os.path.join(webfonts_dir, font)
    download_file(url, path)
