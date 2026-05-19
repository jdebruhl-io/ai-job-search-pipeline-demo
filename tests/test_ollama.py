import requests
r = requests.post('http://localhost:11434/api/generate', json={'model':'qwen3:14b','prompt':'say hi','stream':False})
print(r.status_code, r.text[:200])

