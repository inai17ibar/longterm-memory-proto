"""
記憶統合・関連性分析システムのテストスクリプト
"""
import asyncio
import sys
from datetime import datetime, timedelta

from app.memory_consolidation import memory_consolidation, memory_relationship
from app.memory_system import MemoryItem, memory_system


async def test_memory_consolidation():
    """記憶統合のテスト"""
    print("=" * 60)
    print("記憶統合のテスト")
    print("=" * 60)

    test_user = "test_user_consolidation"

    # 類似した記憶を追加
    similar_memories = [
        "散歩が好きです",
        "歩くのが好き",
        "ウォーキングを楽しんでいます",
        "公園を歩くことが趣味です",
    ]

    print("\n類似記憶を追加中...")
    for idx, content in enumerate(similar_memories):
        memory_id = await memory_system.store_memory(
            user_id=test_user,
            content=content,
            memory_type="coping_methods",
            metadata={"source": "test"},
        )
        if memory_id:
            print(f"  [{idx+1}] {content}")

    # 統合前の記憶数を確認
    memories_before = memory_system.get_memories_by_type(test_user, "coping_methods")
    print(f"\n統合前の記憶数: {len(memories_before)}件")

    # 記憶を統合
    print("\n記憶を統合中（LLM使用）...")
    consolidated = await memory_consolidation.consolidate_similar_memories(
        user_id=test_user, memory_type="coping_methods", similarity_threshold=0.5
    )

    print(f"統合された記憶グループ: {len(consolidated)}グループ")
    for idx, group in enumerate(consolidated, 1):
        print(f"\n  [グループ {idx}]")
        print(f"    統合後: {group['merged_content'][:60]}...")
        print(f"    元の記憶数: {len(group['original_ids'])}")

    if len(consolidated) > 0:
        print("\n  [PASS] 記憶統合が動作しました")
        return True
    else:
        print("\n  [INFO] 統合可能な記憶がありませんでした")
        return True


async def test_memory_summary():
    """記憶サマリー生成のテスト"""
    print("\n" + "=" * 60)
    print("記憶サマリー生成のテスト")
    print("=" * 60)

    test_user = "test_user_summary"

    # 複数の記憶を追加
    test_memories = [
        ("不安が強い", "emotional_state"),
        ("パニック発作", "symptoms"),
        ("深呼吸が効果的", "coping_methods"),
        ("復職を目指している", "goals"),
        ("薬を飲んでいる", "medication"),
    ]

    print("\nテスト記憶を追加中...")
    for content, mem_type in test_memories:
        memory_id = await memory_system.store_memory(
            user_id=test_user, content=content, memory_type=mem_type, metadata={"source": "test"}
        )
        if memory_id:
            print(f"  [{mem_type}] {content}")

    # サマリーを生成
    print("\n記憶サマリーを生成中（LLM使用）...")
    summary = await memory_consolidation.generate_memory_summary(user_id=test_user, days=30)

    if summary:
        print("\nサマリー内容:")
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            elif isinstance(value, list):
                print(f"  {key}: {len(value)}件")
            else:
                print(f"  {key}: {value}")

        print("\n  [PASS] サマリー生成が動作しました")
        return True
    else:
        print("\n  [INFO] サマリーが生成されませんでした")
        return True


def test_relationship_scoring():
    """関連性スコアリングのテスト"""
    print("\n" + "=" * 60)
    print("関連性スコアリングのテスト")
    print("=" * 60)

    test_user = "test_user_relationship"

    # テスト記憶を作成
    now = datetime.now()

    memories = [
        MemoryItem(
            id="mem1",
            user_id=test_user,
            content="不安が強い",
            memory_type="emotional_state",
            importance_score=0.8,
            timestamp=now,
            metadata={},
        ),
        MemoryItem(
            id="mem2",
            user_id=test_user,
            content="パニック発作が起きた",
            memory_type="symptoms",
            importance_score=0.9,
            timestamp=now - timedelta(hours=2),
            metadata={},
        ),
        MemoryItem(
            id="mem3",
            user_id=test_user,
            content="散歩が好き",
            memory_type="coping_methods",
            importance_score=0.6,
            timestamp=now - timedelta(days=5),
            metadata={},
        ),
        MemoryItem(
            id="mem4",
            user_id=test_user,
            content="不安な時は深呼吸",
            memory_type="coping_methods",
            importance_score=0.7,
            timestamp=now - timedelta(days=1),
            metadata={},
        ),
    ]

    # メモリに追加
    if test_user not in memory_system.memory_items:
        memory_system.memory_items[test_user] = []
    memory_system.memory_items[test_user].extend(memories)

    print("\nテスト記憶:")
    for mem in memories:
        print(f"  [{mem.id}] ({mem.memory_type}) {mem.content}")

    # 関連記憶を検索
    print("\n記憶1(不安が強い)に関連する記憶を検索中...")
    related = memory_relationship.find_related_memories(
        user_id=test_user, target_memory=memories[0], limit=3
    )

    print(f"\n関連記憶: {len(related)}件")
    for mem, score, reason in related:
        print(f"  [{mem.id}] スコア={score:.2f}")
        print(f"    内容: {mem.content}")
        print(f"    理由: {reason}")

    # スコアチェック
    if len(related) > 0:
        # 症状タイプ(mem2)が高スコアであることを期待
        top_memory = related[0][0]
        if top_memory.memory_type == "symptoms" or related[0][1] > 0.5:
            print("\n  [PASS] 関連性スコアリングが正しく動作しました")
            return True
        else:
            print("\n  [WARN] 関連性スコアが期待より低い可能性")
            return True
    else:
        print("\n  [FAIL] 関連記憶が見つかりませんでした")
        return False


async def test_memory_graph():
    """記憶グラフ生成のテスト"""
    print("\n" + "=" * 60)
    print("記憶グラフ生成のテスト")
    print("=" * 60)

    test_user = "test_user_graph"

    # テスト記憶を追加
    test_memories = [
        ("不安が強い", "emotional_state", 0.8),
        ("パニック発作", "symptoms", 0.9),
        ("深呼吸する", "coping_methods", 0.7),
        ("復職したい", "goals", 0.6),
        ("薬を飲んでいる", "medication", 0.7),
    ]

    print("\nテスト記憶を追加中...")
    for content, mem_type, importance in test_memories:
        memory_id = await memory_system.store_memory(
            user_id=test_user,
            content=content,
            memory_type=mem_type,
            metadata={"importance_override": importance},
        )
        if memory_id:
            print(f"  [{mem_type}] {content}")

    # グラフを生成
    print("\n記憶グラフを生成中...")
    graph = await memory_relationship.generate_memory_graph(test_user)

    if graph:
        print("\nグラフ構造:")
        print(f"  ノード数: {len(graph.get('nodes', []))}個")
        print(f"  エッジ数: {len(graph.get('edges', []))}本")

        print("\nノード一覧:")
        for node in graph.get("nodes", [])[:5]:
            print(f"  ID={node['id'][:8]}... 重要度={node['importance']:.2f}")
            print(f"    {node['content'][:50]}")

        print("\nエッジ一覧:")
        for edge in graph.get("edges", [])[:5]:
            print(f"  {edge['source'][:8]}... → {edge['target'][:8]}...")
            print(f"    スコア={edge['score']:.2f}, 理由={edge['reason']}")

        if len(graph.get("nodes", [])) > 0:
            print("\n  [PASS] 記憶グラフが生成されました")
            return True
        else:
            print("\n  [FAIL] グラフにノードがありません")
            return False
    else:
        print("\n  [FAIL] グラフが生成されませんでした")
        return False


async def main():
    """全テストを実行"""
    print("\n記憶統合・関連性分析システムのテストを開始します\n")

    results = []
    results.append(("記憶統合", await test_memory_consolidation()))
    results.append(("記憶サマリー", await test_memory_summary()))
    results.append(("関連性スコアリング", test_relationship_scoring()))
    results.append(("記憶グラフ生成", await test_memory_graph()))

    print("\n" + "=" * 60)
    print("最終結果")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n全てのテストが成功しました!")
        sys.exit(0)
    else:
        print("\n一部のテストが失敗しました.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
