# test_execution.py
"""
実行機能の統合テスト
"""

import sys
import json
from executor import PathExecutor, ExecutionContext, create_mock_context
from unit_converter import UnitConverter, UnitAwareCatalog
from provenance import ProvenanceGenerator
from synth_lib import Catalog, synthesize_backward


def test_formula_execution():
    """Formula実行のテスト"""
    print("=" * 60)
    print("テスト1: Formula実行")
    print("=" * 60)

    cat = Catalog.from_dsl('catalog.dsl')
    results = synthesize_backward(cat, src_type='Product', goal_type='CO2')

    assert len(results) > 0, "パスが見つかりません"

    cost, path = results[0]

    # 実行
    context = create_mock_context(
        emission_factor=2.7,
        energy_density=42e6,
        efficiency=0.35
    )

    executor = PathExecutor()
    input_value = 360000  # 360000 J = 100 Wh

    final_result, steps = executor.execute_path(path, input_value, context)

    print(f"入力: {input_value} J")
    print(f"出力: {final_result} kg-CO2")
    print(f"\n実行ステップ:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step.function_id}: {step.input_value} -> {step.output_value}")

    assert final_result is not None, "実行結果がありません"
    assert len(steps) == len(path), "ステップ数が一致しません"

    print("✓ Formula実行テスト: 成功\n")
    return True


def test_unit_conversion():
    """単位変換のテスト"""
    print("=" * 60)
    print("テスト2: 単位変換")
    print("=" * 60)

    converter = UnitConverter()

    # エネルギー変換
    kWh_to_J = converter.convert(1, 'kWh', 'J')
    print(f"1 kWh = {kWh_to_J} J")
    assert abs(kWh_to_J - 3.6e6) < 1, "エネルギー変換が正しくありません"

    # 質量変換
    kg_to_g = converter.convert(1, 'kg', 'g')
    print(f"1 kg = {kg_to_g} g")
    assert kg_to_g == 1000, "質量変換が正しくありません"

    # 温度変換
    C_to_K = converter.convert(0, 'C', 'K')
    print(f"0 C = {C_to_K} K")
    assert abs(C_to_K - 273.15) < 0.01, "温度変換が正しくありません"

    # 変換不可能なケース
    try:
        converter.convert(1, 'kg', 'J')
        assert False, "異なる次元の変換を許可してはいけません"
    except ValueError:
        print("✓ 異なる次元の変換を正しく拒否")

    print("✓ 単位変換テスト: 成功\n")
    return True


def test_provenance_generation():
    """Provenance生成のテスト"""
    print("=" * 60)
    print("テスト3: Provenance生成")
    print("=" * 60)

    cat = Catalog.from_dsl('catalog.dsl')
    results = synthesize_backward(cat, src_type='Product', goal_type='CO2')

    cost, path = results[0]

    # 実行
    context = create_mock_context()
    executor = PathExecutor()
    final_result, steps = executor.execute_path(path, 360000, context)

    # Provenance生成
    generator = ProvenanceGenerator()
    prov = generator.generate_synthesis_provenance(
        synthesis_id='test_001',
        goal='Product->CO2',
        path=path,
        input_value=360000,
        output_value=final_result,
        execution_steps=steps,
        context=context
    )

    assert len(prov.entities) > 0, "エンティティが生成されていません"
    assert len(prov.activities) > 0, "アクティビティが生成されていません"
    assert len(prov.agents) > 0, "エージェントが生成されていません"

    print(f"生成されたProvenance:")
    print(f"  Entities: {len(prov.entities)}")
    print(f"  Activities: {len(prov.activities)}")
    print(f"  Agents: {len(prov.agents)}")

    # Turtle形式に変換
    turtle = prov.to_turtle()
    assert len(turtle) > 0, "Turtle形式への変換が失敗"
    assert 'prov:Entity' in turtle, "Turtle出力にprov:Entityが含まれていません"

    print(f"\nTurtle形式 (先頭部分):")
    print('\n'.join(turtle.split('\n')[:15]))

    # JSON形式に変換
    json_output = prov.to_json()
    prov_dict = json.loads(json_output)
    assert 'entities' in prov_dict, "JSON出力にentitiesが含まれていません"

    print("✓ Provenance生成テスト: 成功\n")
    return True


def test_integrated_execution():
    """統合実行のテスト（全機能）"""
    print("=" * 60)
    print("テスト4: 統合実行（探索+実行+Provenance）")
    print("=" * 60)

    cat = Catalog.from_dsl('catalog.dsl')

    # 1. 探索
    results = synthesize_backward(cat, src_type='Product', goal_type='CO2')
    assert len(results) > 0
    cost, path = results[0]
    print(f"✓ パス探索成功: コスト={cost}")

    # 2. 単位変換（オプション）
    unit_catalog = UnitAwareCatalog(cat)
    augmented_path = unit_catalog.augment_path_with_conversions(
        path, 'Product', 'CO2'
    )
    print(f"✓ 単位変換チェック完了: パス長={len(augmented_path)}")

    # 3. 実行
    context = create_mock_context()
    executor = PathExecutor()
    final_result, steps = executor.execute_path(path, 360000, context)
    assert final_result is not None
    print(f"✓ 実行成功: 入力=360000 J, 出力={final_result} kg-CO2")

    # 4. Provenance生成
    generator = ProvenanceGenerator()
    prov = generator.generate_synthesis_provenance(
        synthesis_id='integrated_test',
        goal='Product->CO2',
        path=path,
        input_value=360000,
        output_value=final_result,
        execution_steps=steps,
        context=context
    )
    assert len(prov.entities) > 0
    print(f"✓ Provenance生成成功: {len(prov.entities)} entities")

    # 5. 結果の検証
    assert len(steps) == len(path)
    print(f"✓ 全体検証成功: {len(steps)}ステップ実行")

    print("\n✓ 統合実行テスト: 成功\n")
    return True


def test_execution_with_different_inputs():
    """異なる入力値でのテスト"""
    print("=" * 60)
    print("テスト5: 異なる入力値での実行")
    print("=" * 60)

    cat = Catalog.from_dsl('catalog.dsl')
    results = synthesize_backward(cat, src_type='Product', goal_type='CO2')
    cost, path = results[0]

    context = create_mock_context()
    executor = PathExecutor()

    # 複数の入力値でテスト
    test_inputs = [100000, 360000, 1000000]

    for input_val in test_inputs:
        final_result, steps = executor.execute_path(path, input_val, context)
        print(f"入力={input_val:,} J -> 出力={final_result:.4f} kg-CO2")

        assert final_result is not None
        assert len(steps) == len(path)

    print("✓ 複数入力値テスト: 成功\n")
    return True


def main():
    """すべてのテストを実行"""
    print("\n" + "=" * 60)
    print("実行機能 統合テストスイート")
    print("=" * 60 + "\n")

    tests = [
        test_formula_execution,
        test_unit_conversion,
        test_provenance_generation,
        test_integrated_execution,
        test_execution_with_different_inputs,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"\n✗ テスト失敗: {test.__name__}")
            print(f"  エラー: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ テスト例外: {test.__name__}")
            print(f"  例外: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print("テスト結果")
    print("=" * 60)
    print(f"成功: {passed}/{len(tests)}")
    print(f"失敗: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✓ すべてのテストが成功しました！")
        return 0
    else:
        print(f"\n✗ {failed}個のテストが失敗しました")
        return 1


if __name__ == '__main__':
    sys.exit(main())
