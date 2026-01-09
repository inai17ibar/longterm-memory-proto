"""
記憶品質フィルタリングのテストスクリプト
"""
import sys
import asyncio
from app.memory_system import memory_system

async def test_quality_filtering():
    """記憶品質フィルタリングのテスト"""
    print("=" * 60)
    print("記憶品質フィルタリングのテスト")
    print("=" * 60)

    test_user = "test_user_quality"

    test_cases = [
        {
            "content": "こんにちは",
            "memory_type": "emotional_state",
            "should_reject": True,
            "reason": "短すぎる"
        },
        {
            "content": "はい",
            "memory_type": "concerns",
            "should_reject": True,
            "reason": "一般的すぎる表現"
        },
        {
            "content": "今日は不安が強くて辛かったです",
            "memory_type": "emotional_state",
            "should_reject": False,
            "reason": "有効な記憶"
        },
        {
            "content": "散歩が好きです",
            "memory_type": "coping_methods",
            "should_reject": False,
            "reason": "有効な記憶"
        },
        {
            "content": "散歩が好きです",  # 重複
            "memory_type": "coping_methods",
            "should_reject": True,
            "reason": "重複（2回目）"
        },
        {
            "content": "散歩が好き",  # 類似
            "memory_type": "coping_methods",
            "should_reject": True,
            "reason": "類似重複"
        }
    ]

    passed = 0
    failed = 0

    print("\n記憶品質チェック:")
    for idx, test in enumerate(test_cases, 1):
        memory_id = await memory_system.store_memory(
            user_id=test_user,
            content=test["content"],
            memory_type=test["memory_type"],
            metadata={"test": True}
        )

        was_rejected = (memory_id == "" or memory_id is None)

        if was_rejected == test["should_reject"]:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

        action = "拒否" if was_rejected else "保存"
        expected = "拒否されるべき" if test["should_reject"] else "保存されるべき"

        print(f"\n  [テスト {idx}] {status}")
        print(f"    内容: '{test['content']}'")
        print(f"    理由: {test['reason']}")
        print(f"    期待: {expected}")
        print(f"    結果: {action}")

    print(f"\n{'=' * 60}")
    print(f"結果: {passed}件成功 / {failed}件失敗")
    print("=" * 60)

    return failed == 0


async def test_importance_threshold():
    """重要度閾値フィルタリングのテスト"""
    print("\n" + "=" * 60)
    print("重要度閾値フィルタリングのテスト")
    print("=" * 60)

    test_user = "test_user_importance"

    test_cases = [
        {
            "content": "パニック発作が起きて苦しかった",
            "memory_type": "symptoms",
            "should_store": True,
            "expected_importance": "高い (>0.7)"
        },
        {
            "content": "不安で眠れない",
            "memory_type": "emotional_state",
            "should_store": True,
            "expected_importance": "中程度 (0.4-0.7)"
        },
        {
            "content": "散歩した",
            "memory_type": "daily_routine",
            "should_store": True,  # 短いが意味はあるので保存される可能性
            "expected_importance": "低い (0.2-0.4)"
        }
    ]

    print("\n重要度による保存テスト:")
    stored_count = 0

    for idx, test in enumerate(test_cases, 1):
        memory_id = await memory_system.store_memory(
            user_id=test_user,
            content=test["content"],
            memory_type=test["memory_type"],
            metadata={"test": True}
        )

        was_stored = bool(memory_id)

        print(f"\n  [テスト {idx}]")
        print(f"    内容: '{test['content']}'")
        print(f"    タイプ: {test['memory_type']}")
        print(f"    期待重要度: {test['expected_importance']}")
        print(f"    結果: {'保存' if was_stored else '拒否'}")

        if was_stored:
            stored_count += 1

    print(f"\n保存された記憶: {stored_count}件")

    # 最低1件は保存されるはず
    if stored_count > 0:
        print("  [PASS] 重要度フィルタリングが動作しました")
        return True
    else:
        print("  [FAIL] 全ての記憶が拒否されました")
        return False


async def test_similarity_detection():
    """類似度検出のテスト"""
    print("\n" + "=" * 60)
    print("類似度検出のテスト")
    print("=" * 60)

    test_user = "test_user_similarity"

    # 元の記憶
    original = "不安で夜眠れないことが多いです"
    await memory_system.store_memory(
        user_id=test_user,
        content=original,
        memory_type="symptoms",
        metadata={"test": True}
    )
    print(f"\n元の記憶: '{original}'")

    # 類似記憶のテストケース
    test_cases = [
        {
            "content": "不安で夜眠れないことが多いです",  # 完全一致
            "should_reject": True,
            "label": "完全一致"
        },
        {
            "content": "不安で夜に眠れないことが多い",  # 90%以上類似
            "should_reject": True,
            "label": "90%以上類似"
        },
        {
            "content": "不安があります",  # 部分的に類似
            "should_reject": False,
            "label": "部分的類似（保存可）"
        },
        {
            "content": "朝は元気です",  # 全く異なる
            "should_reject": False,
            "label": "異なる内容（保存可）"
        }
    ]

    passed = 0
    failed = 0

    print("\n類似度チェック:")
    for idx, test in enumerate(test_cases, 1):
        memory_id = await memory_system.store_memory(
            user_id=test_user,
            content=test["content"],
            memory_type="symptoms",
            metadata={"test": True}
        )

        was_rejected = not bool(memory_id)

        if was_rejected == test["should_reject"]:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

        print(f"\n  [テスト {idx}] {status} - {test['label']}")
        print(f"    内容: '{test['content']}'")
        print(f"    期待: {'拒否' if test['should_reject'] else '保存'}")
        print(f"    結果: {'拒否' if was_rejected else '保存'}")

    print(f"\n{'=' * 60}")
    print(f"結果: {passed}件成功 / {failed}件失敗")
    print("=" * 60)

    return failed == 0


async def main():
    """全テストを実行"""
    print("\n記憶品質フィルタリングのテストを開始します\n")

    results = []
    results.append(("品質フィルタリング", await test_quality_filtering()))
    results.append(("重要度閾値", await test_importance_threshold()))
    results.append(("類似度検出", await test_similarity_detection()))

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
