import urllib.request
import json
try:
    print(urllib.request.urlopen('http://localhost:3001/api/ml/form/73822').read().decode())
except Exception as e:
    print(f"Error checking ml endpoint: {e}")
