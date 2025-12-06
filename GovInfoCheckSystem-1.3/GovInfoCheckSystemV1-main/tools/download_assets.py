import os
import requests

def download_file(url, filepath):
    print(f"Downloading {url} to {filepath}...")
    try:
        response = requests.get(url, timeout=10)
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

# Files to download
files = [
    {
        'url': 'https://cdn.bootcdn.net/ajax/libs/socket.io/4.5.4/socket.io.min.js',
        'path': os.path.join(plugin_static_dir, 'js', 'socket.io.min.js')
    },
    {
        'url': 'https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/css/all.min.css',
        'path': os.path.join(plugin_static_dir, 'css', 'all.min.css')
    },
    {
        'url': 'http://cdn.tailwindcss.com', # Try HTTP
        'path': os.path.join(plugin_static_dir, 'js', 'tailwindcss.js')
    }
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for file_info in files:
    if os.path.exists(file_info['path']) and os.path.getsize(file_info['path']) > 0:
        print(f"Skipping {file_info['path']} (already exists)")
        continue
        
    print(f"Downloading {file_info['url']} to {file_info['path']}...")
    try:
        response = requests.get(file_info['url'], headers=headers, timeout=30)
        response.raise_for_status()
        with open(file_info['path'], 'wb') as f:
            f.write(response.content)
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")
