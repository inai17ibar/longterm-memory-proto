import requests
import json

# チャットAPIをテスト
url = "http://127.0.0.1:8001/api/chat"
data = {
    "user_id": "test123",
    "message": "こんにちは、私は田中と申します。最近、不安な気持ちが続いています。"
}

print("Sending request...")
response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
