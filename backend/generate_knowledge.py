"""
メンタルヘルスの基本知識をLLMで生成して知識ベースに登録するスクリプト
"""

import json
import os
from datetime import datetime

import openai
from dotenv import load_dotenv

from app.knowledge_base import KnowledgeItem, knowledge_base

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 生成する知識のカテゴリとトピック
KNOWLEDGE_TOPICS = {
    "cbt_technique": [
        "認知の歪みパターンと対処法",
        "自動思考の特定と記録",
        "思考記録表の使い方",
        "認知再構成の手順",
        "破局的思考への対処",
    ],
    "dbt_technique": [
        "マインドフルネス瞑想の基本",
        "感情調整スキル",
        "苦痛耐性スキル",
        "対人関係効果性スキル",
    ],
    "symptom_management": [
        "不安症状への対処法",
        "パニック発作時の対処",
        "うつ症状の日常管理",
        "不眠への対処法",
        "過覚醒状態の落ち着かせ方",
        "解離症状への対処",
    ],
    "coping_strategy": [
        "グラウンディング技法",
        "呼吸法とリラクセーション",
        "5-4-3-2-1法（感覚を使った落ち着き法）",
        "セルフコンパッション",
        "アクティベーション（行動活性化）",
        "ジャーナリング",
    ],
    "self_care": [
        "睡眠衛生の基本",
        "運動とメンタルヘルス",
        "栄養とメンタルヘルス",
        "ソーシャルサポートの活用",
        "ストレス管理の基本",
    ],
    "crisis_support": [
        "自殺念慮への対処",
        "自傷行為の代替スキル",
        "危機時の安全計画",
        "緊急連絡先リスト",
    ],
}


def generate_knowledge_item(category: str, topic: str) -> KnowledgeItem:
    """LLMを使って特定のトピックの知識を生成"""

    prompt = f"""
あなたはメンタルヘルスの専門家です。以下のトピックについて、カウンセリング現場で使える実践的な知識をまとめてください。

カテゴリ: {category}
トピック: {topic}

以下の形式でJSONを返してください：
{{
  "title": "タイトル（日本語、簡潔に）",
  "content": "詳しい説明（300-500文字、実践的で具体的に。箇条書きを含めても良い）",
  "tags": ["タグ1", "タグ2", "タグ3"],
  "relevance_keywords": ["キーワード1", "キーワード2", "キーワード3"]
}}

重要：
- ユーザーが実際に試せる具体的な方法を含めてください
- 専門用語は平易な言葉で説明してください
- 共感的で優しいトーンで書いてください
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはメンタルヘルスの専門家で、実践的な知識を提供します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.7,
        )

        text = response.choices[0].message.content.strip()

        # JSONを抽出
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        data = json.loads(text.strip())

        item_id = f"{category}_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"

        return KnowledgeItem(
            id=item_id,
            category=category,
            title=data["title"],
            content=data["content"],
            tags=data["tags"],
            relevance_keywords=data["relevance_keywords"],
            created_at=datetime.now().isoformat(),
        )

    except Exception as e:
        print(f"Error generating knowledge for {topic}: {e}")
        return None


def main():
    """知識ベースを生成"""
    print("メンタルヘルス知識ベースの生成を開始します...")
    print(f"総トピック数: {sum(len(topics) for topics in KNOWLEDGE_TOPICS.values())}")

    generated_count = 0

    for category, topics in KNOWLEDGE_TOPICS.items():
        print(f"\nカテゴリ: {category}")

        for topic in topics:
            print(f"  - 生成中: {topic}...", end=" ")

            item = generate_knowledge_item(category, topic)

            if item:
                knowledge_base.add_knowledge(item)
                generated_count += 1
                print("OK")
            else:
                print("ERROR")

    print(f"\n完了! {generated_count}件の知識を生成しました。")

    # 統計表示
    stats = knowledge_base.get_stats()
    print("\n統計:")
    print(f"  総件数: {stats['total_items']}")
    print("  カテゴリ別:")
    for cat, count in stats["by_category"].items():
        print(f"    - {cat}: {count}件")


if __name__ == "__main__":
    main()
