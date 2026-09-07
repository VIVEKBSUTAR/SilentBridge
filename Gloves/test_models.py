import urllib.request
import json

# REMOVED SECRET: API Key has been removed for security.
# Add your key back locally if needed.
api_key = "YOUR_API_KEY_HERE"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        models = [m['name'] for m in data.get('models', [])]
        print("Available models:")
        for m in models:
            if 'gemini' in m:
                print(m)
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode())
except Exception as e:
    print(f"Error: {e}")
