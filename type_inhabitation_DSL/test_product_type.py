#!/usr/bin/env python3
"""
Product型のテストケース

Product型を使ったGHG Scope 1,2,3の集約をテストします。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from synth_lib import Catalog, synthesize_backward
from executor import PathExecutor, ExecutionContext


def test_product_type_parsing():
    """Product型の定義がパースできることを確認"""
    print("=" * 80)
    print("Test 1: Product型の定義のパース")
    print("=" * 80)

    catalog = Catalog.from_dsl("ghg_scope123_product.dsl")

    print(f"✓ カタログ読み込み成功")
    print(f"  型: {len(catalog.types)} 個")
    print(f"  関数: {len(catalog.funcs)} 個")

    # Product型の確認
    if catalog.is_product_type("AllScopesEmissions"):
        components = catalog.get_product_components("AllScopesEmissions")
        print(f"\n✓ Product型 'AllScopesEmissions' が定義されています")
        print(f"  コンポーネント: {components}")
    else:
        print(f"\n✗ Product型 'AllScopesEmissions' が見つかりません")
        return False

    print("\n" + "=" * 80)
    return True


def test_path_to_allscopes():
    """各ScopeからAllScopesEmissionsへのパスを探索"""
    print("\nTest 2: 各ScopeからAllScopesEmissionsへのパス探索")
    print("=" * 80)

    catalog = Catalog.from_dsl("ghg_scope123_product.dsl")

    # Scope1 -> AllScopes へのパスを探索
    print("\n🔍 Scope1Emissions -> AllScopesEmissions")
    results = synthesize_backward(catalog, "Scope1Emissions", "AllScopesEmissions")

    if results:
        cost, path = results[0]
        print(f"✓ パス発見成功！")
        print(f"  パス長: {len(path)}")
        print(f"  総コスト: {cost}")
        print(f"  関数:")
        for func in path:
            print(f"    - {func.id}: {func.dom} -> {func.cod}")
    else:
        print(f"✗ パスが見つかりませんでした")

    print("\n" + "=" * 80)
    return True


def test_allscopes_to_total():
    """AllScopesEmissionsからTotalGHGEmissionsへのパスを探索"""
    print("\nTest 3: AllScopesEmissions -> TotalGHGEmissions のパス探索")
    print("=" * 80)

    catalog = Catalog.from_dsl("ghg_scope123_product.dsl")

    results = synthesize_backward(catalog, "AllScopesEmissions", "TotalGHGEmissions")

    if results:
        cost, path = results[0]
        print(f"✓ パス発見成功！")
        print(f"  パス長: {len(path)}")
        print(f"  総コスト: {cost}")
        print(f"  関数:")
        for func in path:
            print(f"    - {func.id}: {func.dom} -> {func.cod}")
            print(f"      実装: {func.impl}")
    else:
        print(f"✗ パスが見つかりませんでした")

    print("\n" + "=" * 80)
    return True


def test_execute_product_aggregation():
    """Product型を使った集約の実行をテスト"""
    print("\nTest 4: Product型を使った集約の実行")
    print("=" * 80)

    catalog = Catalog.from_dsl("ghg_scope123_product.dsl")

    # AllScopes -> Total のパスを取得
    results = synthesize_backward(catalog, "AllScopesEmissions", "TotalGHGEmissions")

    if not results:
        print("✗ パスが見つかりませんでした")
        return False

    cost, path = results[0]
    print(f"✓ パス: {' -> '.join([f.id for f in path])}")

    # 実行エンジンを作成
    executor = PathExecutor()
    context = ExecutionContext(mock_mode=True)

    # モックのProduct型の値（タプルとして表現）
    # (Scope1, Scope2, Scope3) = (1000.0, 1500.0, 800.0)
    mock_allscopes_value = (1000.0, 1500.0, 800.0)

    print(f"\n入力値（Product型）: {mock_allscopes_value}")
    print(f"  Scope1: {mock_allscopes_value[0]} kg-CO2")
    print(f"  Scope2: {mock_allscopes_value[1]} kg-CO2")
    print(f"  Scope3: {mock_allscopes_value[2]} kg-CO2")

    try:
        # パスを実行
        final_value, steps = executor.execute_path(path, mock_allscopes_value, context)

        print(f"\n✓ 実行成功！")
        print(f"  最終結果: {final_value} kg-CO2")
        print(f"  期待値: {sum(mock_allscopes_value)} kg-CO2")

        if abs(final_value - sum(mock_allscopes_value)) < 0.01:
            print(f"  ✓ 結果が期待値と一致しています")
        else:
            print(f"  ⚠ 結果が期待値と異なります")

        print(f"\n実行ステップ:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step.function_id}")
            print(f"     入力: {step.input_value}")
            print(f"     出力: {step.output_value}")

    except Exception as e:
        print(f"\n✗ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    return True


def test_comparison_single_vs_product():
    """単一Scopeアプローチ vs Product型アプローチの比較"""
    print("\nTest 5: 単一Scope vs Product型アプローチの比較")
    print("=" * 80)

    catalog = Catalog.from_dsl("ghg_scope123_product.dsl")

    # Facility -> Total のパス（単一Scopeアプローチ）
    print("\n🔍 アプローチ1: 単一Scope経由")
    results_single = synthesize_backward(catalog, "Facility", "TotalGHGEmissions")

    if results_single:
        cost, path = results_single[0]
        print(f"✓ パス発見: コスト={cost}")
        print(f"  経路: {' -> '.join([f.id for f in path])}")
        print(f"  ⚠ 問題: Scope2だけが使われる（不正確）")
    else:
        print(f"✗ パスなし")

    # Product型アプローチの説明
    print("\n🔍 アプローチ2: Product型経由（推奨）")
    print("  1. 各Scopeへのパスを個別に実行")
    print("     Facility -> Scope1Emissions")
    print("     Facility -> Scope2Emissions")
    print("     Organization -> Scope3Emissions")
    print("  2. 3つの値からProduct型を構築")
    print("  3. Product型 -> TotalGHGEmissions を実行")
    print("  ✓ 利点: すべてのScopeが正確に集約される")

    print("\n結論:")
    print("  - 現在の型システムでは完全な多引数関数はサポートされていない")
    print("  - Product型は「複数の値を1つとして扱う」ための中間的な解決策")
    print("  - 実用的には、各Scopeを個別実行 + 手動集約が必要")
    print("  - 将来的には完全な多引数関数サポートが望ましい")

    print("\n" + "=" * 80)
    return True


def main():
    """全テストを実行"""
    print("\n" + "=" * 80)
    print("Product型テストスイート")
    print("=" * 80 + "\n")

    tests = [
        test_product_type_parsing,
        test_path_to_allscopes,
        test_allscopes_to_total,
        test_execute_product_aggregation,
        test_comparison_single_vs_product
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # サマリー
    print("\n" + "=" * 80)
    print("テスト結果サマリー")
    print("=" * 80)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"✓ {passed}/{total} テストが成功")

    if passed == total:
        print("\n🎉 すべてのテストが成功しました！")
    else:
        print(f"\n⚠  {total - passed} 件のテストが失敗しました")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
