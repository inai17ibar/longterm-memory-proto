"""
重要度計算と時間減衰のテストスクリプト
"""
import sys
from datetime import datetime, timedelta
from app.memory_system import MemoryItem, MemoryImportanceCalculator

def test_importance_calculation():
    """重要度計算のテスト"""
    print("=" * 60)
    print("重要度計算のテスト")
    print("=" * 60)

    test_cases = [
        {
            "content": "不安で苦しい、もう限界です",
            "memory_type": "emotional_state",
            "expected_range": (0.8, 1.0),
            "description": "高い感情強度 + 重要なタイプ"
        },
        {
            "content": "少し心配です",
            "memory_type": "concerns",
            "expected_range": (0.5, 0.8),
            "description": "中程度の感情強度"
        },
        {
            "content": "散歩が好きです",
            "memory_type": "personality",
            "expected_range": (0.2, 0.6),
            "description": "低い感情強度 + 低優先度タイプ"
        },
        {
            "content": "パニック発作が起きた",
            "memory_type": "symptoms",
            "expected_range": (0.8, 1.0),
            "description": "症状タイプ + 高感情強度"
        }
    ]

    passed = 0
    failed = 0

    for idx, test in enumerate(test_cases, 1):
        score = MemoryImportanceCalculator.calculate_importance(
            test["content"],
            test["memory_type"],
            {"timestamp": datetime.now().isoformat()}
        )

        min_expected, max_expected = test["expected_range"]
        is_pass = min_expected <= score <= max_expected

        status = "PASS" if is_pass else "FAIL"
        print(f"\n[テスト {idx}] {status}")
        print(f"  説明: {test['description']}")
        print(f"  内容: {test['content']}")
        print(f"  タイプ: {test['memory_type']}")
        print(f"  計算結果: {score:.2f}")
        print(f"  期待範囲: {min_expected:.2f} - {max_expected:.2f}")

        if is_pass:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"結果: {passed}件成功 / {failed}件失敗")
    print("=" * 60)

    return failed == 0


def test_time_decay():
    """時間減衰のテスト"""
    print("\n" + "=" * 60)
    print("時間減衰のテスト")
    print("=" * 60)

    # テスト用の記憶を作成
    base_score = 0.9
    test_cases = [
        {"days_ago": 0, "expected_factor": 1.0, "label": "今日"},
        {"days_ago": 1, "expected_factor": 0.95, "label": "1日前"},
        {"days_ago": 7, "expected_factor": 0.85, "label": "1週間前"},
        {"days_ago": 30, "expected_factor": 0.65, "label": "1ヶ月前"},
        {"days_ago": 90, "expected_factor": 0.45, "label": "3ヶ月前"},
        {"days_ago": 365, "expected_factor": 0.25, "label": "1年前"},
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        timestamp = datetime.now() - timedelta(days=test["days_ago"])
        memory = MemoryItem(
            id="test_id",
            user_id="test_user",
            content="テスト記憶",
            memory_type="emotional_state",
            importance_score=base_score,
            timestamp=timestamp,
            metadata={}
        )

        current_importance = memory.get_current_importance()
        expected_score = base_score * test["expected_factor"]
        tolerance = 0.02  # 許容誤差

        is_pass = abs(current_importance - expected_score) <= tolerance

        status = "PASS" if is_pass else "FAIL"
        print(f"\n[{test['label']}] {status}")
        print(f"  基本重要度: {base_score:.2f}")
        print(f"  減衰係数: {test['expected_factor']:.2f}")
        print(f"  期待値: {expected_score:.2f}")
        print(f"  計算結果: {current_importance:.2f}")

        if is_pass:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"結果: {passed}件成功 / {failed}件失敗")
    print("=" * 60)

    return failed == 0


def test_persistent_types():
    """減衰しにくいタイプのテスト"""
    print("\n" + "=" * 60)
    print("減衰しにくいタイプのテスト")
    print("=" * 60)

    base_score = 0.8
    days_ago = 365  # 1年前

    persistent_types = ['symptoms', 'goals', 'medication', 'personality', 'work_status']
    non_persistent_types = ['emotional_state', 'concerns']

    print("\n[減衰しにくいタイプ]")
    for memory_type in persistent_types:
        timestamp = datetime.now() - timedelta(days=days_ago)
        memory = MemoryItem(
            id="test_id",
            user_id="test_user",
            content="テスト記憶",
            memory_type=memory_type,
            importance_score=base_score,
            timestamp=timestamp,
            metadata={}
        )
        current = memory.get_current_importance()
        print(f"  {memory_type}: {base_score:.2f} → {current:.2f} (最低70%維持)")

    print("\n[通常の減衰タイプ]")
    for memory_type in non_persistent_types:
        timestamp = datetime.now() - timedelta(days=days_ago)
        memory = MemoryItem(
            id="test_id",
            user_id="test_user",
            content="テスト記憶",
            memory_type=memory_type,
            importance_score=base_score,
            timestamp=timestamp,
            metadata={}
        )
        current = memory.get_current_importance()
        print(f"  {memory_type}: {base_score:.2f} → {current:.2f}")

    print("=" * 60)


def main():
    """全テストを実行"""
    print("\n重要度システムのテストを開始します\n")

    results = []
    results.append(("重要度計算", test_importance_calculation()))
    results.append(("時間減衰", test_time_decay()))

    test_persistent_types()

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
    main()
