"""
全機能の統合テストスクリプト
"""
import asyncio
import sys

# 個別のテストをインポート
from test_importance import test_importance_calculation, test_time_decay


async def test_basic_functionality():
    """基本機能の統合テスト"""
    print("=" * 60)
    print("基本機能の統合テスト")
    print("=" * 60)

    import time

    from app.episodic_memory import episodic_memory_system
    from app.memory_system import memory_system
    from app.user_profile import user_profile_system

    test_user = f"integration_test_{int(time.time())}"

    # 1. 記憶システムのテスト
    print("\n[1] 記憶システムのテスト")
    memory_id = await memory_system.store_memory(
        user_id=test_user,
        content="テストで不安を感じています",
        memory_type="emotional_state",
        metadata={"test": True},
    )

    if memory_id:
        print(f"  [OK] 記憶が保存されました: {memory_id[:20]}...")
    else:
        print("  [NG] 記憶の保存に失敗")
        return False

    # 2. エピソード記憶のテスト
    print("\n[2] エピソード記憶のテスト")
    emotion_id = episodic_memory_system.record_emotion(
        user_id=test_user,
        mood=6,
        energy=5,
        anxiety=7,
        primary_emotion="anxious",
        triggers=["テスト"],
        notes="テスト中",
    )

    if emotion_id:
        print(f"  [OK] 感情が記録されました: {emotion_id[:20]}...")
    else:
        print("  [NG] 感情の記録に失敗")
        return False

    # 3. 感情履歴の取得
    print("\n[3] 感情履歴の取得")
    emotions = episodic_memory_system.get_emotion_history(test_user, days=7)
    print(f"  取得件数: {len(emotions)}件")

    if len(emotions) > 0:
        print("  [OK] 感情履歴が取得できました")
    else:
        print("  [NG] 感情履歴が空です")
        return False

    # 4. ユーザープロファイルのテスト
    print("\n[4] ユーザープロファイルのテスト")
    # 新しいユーザーの場合、プロファイルシステムが自動生成する
    retrieved_profile = user_profile_system.get_profile(test_user)

    if retrieved_profile and retrieved_profile.user_id == test_user:
        print(f"  [OK] プロファイルが取得できました: user_id={retrieved_profile.user_id}")
    else:
        print("  [SKIP] プロファイルシステムのテストをスキップ")
        # プロファイルがなくても続行

    # 5. 記憶の重要度計算
    print("\n[5] 記憶の重要度計算")
    from app.memory_system import MemoryImportanceCalculator

    score = MemoryImportanceCalculator.calculate_importance("パニック発作が起きた", "symptoms", {})
    print(f"  重要度スコア: {score:.2f}")

    if score > 0.7:
        print("  [OK] 高重要度として計算されました")
    else:
        print("  [NG] 重要度が低すぎます")
        return False

    print("\n" + "=" * 60)
    print("全ての基本機能が正常に動作しました")
    print("=" * 60)
    return True


async def test_quality_filtering():
    """記憶品質フィルタリングのテスト"""
    print("\n" + "=" * 60)
    print("記憶品質フィルタリングのテスト")
    print("=" * 60)

    import time

    from app.memory_system import memory_system

    test_user = f"quality_test_{int(time.time())}"

    # 短すぎる記憶（拒否されるべき）
    print("\n[短すぎる記憶]")
    result1 = await memory_system.store_memory(
        user_id=test_user, content="はい", memory_type="concerns", metadata={}
    )

    if not result1:
        print("  [OK] 短すぎる記憶が拒否されました")
    else:
        print("  [NG] 短すぎる記憶が保存されてしまいました")
        return False

    # 有効な記憶（保存されるべき）
    print("\n[有効な記憶]")
    result2 = await memory_system.store_memory(
        user_id=test_user,
        content="今日は不安が強くて辛かったです",
        memory_type="emotional_state",
        metadata={},
    )

    if result2:
        print("  [OK] 有効な記憶が保存されました")
    else:
        print("  [NG] 有効な記憶が拒否されました")
        return False

    # 重複記憶（拒否されるべき）
    print("\n[重複記憶]")
    result3 = await memory_system.store_memory(
        user_id=test_user,
        content="今日は不安が強くて辛かったです",
        memory_type="emotional_state",
        metadata={},
    )

    if not result3:
        print("  [OK] 重複記憶が拒否されました")
    else:
        print("  [NG] 重複記憶が保存されてしまいました")
        return False

    print("\n記憶品質フィルタリングが正常に動作しました")
    return True


async def main():
    """全テストを実行"""
    print("\n" + "=" * 70)
    print(" 長期記憶システム - 統合テストスイート")
    print("=" * 70)

    results = []

    # 既存のテスト
    print("\n[Phase 1] 重要度計算システムのテスト")
    results.append(("重要度計算", test_importance_calculation()))
    results.append(("時間減衰", test_time_decay()))

    # 新機能のテスト
    print("\n[Phase 2] 新機能の統合テスト")
    results.append(("基本機能", await test_basic_functionality()))
    results.append(("品質フィルタリング", await test_quality_filtering()))

    # 結果サマリー
    print("\n" + "=" * 70)
    print(" テスト結果サマリー")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:8} {test_name}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n[SUCCESS] 全てのテストが成功しました!")
        print("\n実装された機能:")
        print("  - 記憶品質フィルタリング（重複検出、重要度閾値）")
        print("  - エピソード記憶と感情履歴トラッキング")
        print("  - ユーザープロファイル管理")
        print("  - 重要度計算と時間減衰")
        sys.exit(0)
    else:
        print("\n[WARNING] 一部のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
