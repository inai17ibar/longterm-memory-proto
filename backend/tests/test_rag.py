"""
RAGシステムのテストスクリプト
"""

import requests

# テストメッセージ
test_cases = [{"user_id": "test_rag_user_001", "message": "不安で眠れない"}]

print("=" * 60)
print("RAGシステムのテスト")
print("=" * 60)

for idx, test_case in enumerate(test_cases, 1):
    print(f"\n【テストケース {idx}】")
    print(f"ユーザーメッセージ: {test_case['message']}")
    print("-" * 60)

    try:
        response = requests.post("http://localhost:8000/api/chat", json=test_case, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print("\nAI応答:")
            print(data["response"])
            print(f"\n応答パターン: {data['response_type']}")
            print(f"ユーザー情報更新: {data['user_info_updated']}")
        else:
            print(f"エラー: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"エラー: {e}")

print("\n" + "=" * 60)
print("テスト完了")
print("=" * 60)

# 知識ベース検索のテスト
print("\n知識ベース検索テスト:")
print("-" * 60)

try:
    kb_response = requests.get(
        "http://localhost:8000/api/knowledge/search",
        params={"query": "不安で眠れない", "limit": 3},
        timeout=10,
    )

    if kb_response.status_code == 200:
        kb_data = kb_response.json()
        print(f"\n検索クエリ: {kb_data['query']}")
        print(f"ヒット数: {len(kb_data['knowledge'])}件\n")

        for idx, item in enumerate(kb_data["knowledge"], 1):
            print(f"{idx}. 【{item['title']}】")
            print(f"   カテゴリ: {item['category']}")
            print(f"   内容: {item['content'][:150]}...")
            print()

except Exception as e:
    print(f"エラー: {e}")
