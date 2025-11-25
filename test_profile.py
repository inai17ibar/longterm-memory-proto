import requests
import json

user_id = "test123"

# プロファイル取得
print("=== プロファイル取得 ===")
response = requests.get(f"http://127.0.0.1:8001/api/profile/{user_id}")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
else:
    print(response.text)

# ユーザー状態取得
print("\n=== ユーザー状態取得 ===")
response = requests.get(f"http://127.0.0.1:8001/api/state/{user_id}")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
else:
    print(response.text)
