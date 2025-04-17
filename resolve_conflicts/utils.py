import re
import requests

def find_conflicts(file_paths):
    conflicts = {}
    for path in file_paths:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if "<<<<<<<" in content:
            conflicts[path] = content
    return conflicts

def send_to_ai(conflicts, api_key):
    # Format payload
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are an AI that resolves Git merge conflicts."},
            {"role": "user", "content": f"Resolve these conflicts:\n\n{conflicts}"}
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    # Assume content is a dict {filename: resolved_text}
    return parse_response(result['choices'][0]['message']['content'])

def parse_response(response_text):
    # Implement your own logic for parsing the response
    # This might be custom if your app returns raw text or JSON
    # For now we assume it's simple dict-like format
    import json
    return json.loads(response_text)

def apply_fixes(fixed_files):
    for path, new_content in fixed_files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
