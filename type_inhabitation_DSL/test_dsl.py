# test_dsl.py
"""
DSLパーサーと型合成システムの統合テスト
"""

import sys
from dsl_parser import parse_dsl_string, DSLParser
from synth_lib import Catalog, synthesize_backward

def test_dsl_parsing():
    """DSLパーサーの基本機能テスト"""
    print("=" * 60)
    print("テスト1: DSLパーサーの基本機能")
    print("=" * 60)

    dsl_content = """
    # テスト用DSL
    type A
    type B [unit=kg]
    type C [unit=m, range=>0]

    fn f1 {
      sig: A -> B
      impl: formula("b = a * 2")
      cost: 1
      confidence: 0.9
    }

    fn f2 {
      sig: B -> C
      impl: sparql("SELECT ?b ?c WHERE { ?b :prop ?c }")
      cost: 2
      confidence: 0.95
    }
    """

    parser = DSLParser()
    parser.parse(dsl_content)

    assert len(parser.types) == 3, f"Expected 3 types, got {len(parser.types)}"
    assert len(parser.functions) == 2, f"Expected 2 functions, got {len(parser.functions)}"

    # 型のチェック
    type_names = [t.name for t in parser.types]
    assert 'A' in type_names
    assert 'B' in type_names
    assert 'C' in type_names

    # 型属性のチェック
    type_b = next(t for t in parser.types if t.name == 'B')
    assert type_b.attributes.get('unit') == 'kg'

    type_c = next(t for t in parser.types if t.name == 'C')
    assert type_c.attributes.get('unit') == 'm'
    assert type_c.attributes.get('range') == '>0'

    # 関数のチェック
    f1 = next(f for f in parser.functions if f.id == 'f1')
    assert f1.sig == 'A -> B'
    assert f1.cost == 1.0
    assert f1.confidence == 0.9
    assert f1.impl['kind'] == 'formula'

    f2 = next(f for f in parser.functions if f.id == 'f2')
    assert f2.sig == 'B -> C'
    assert f2.cost == 2.0
    assert f2.confidence == 0.95
    assert f2.impl['kind'] == 'sparql'

    print("✓ DSLパーサーの基本機能: 成功")
    return True

def test_catalog_integration():
    """カタログへの変換と型合成のテスト"""
    print("\n" + "=" * 60)
    print("テスト2: カタログ変換と型合成")
    print("=" * 60)

    dsl_content = """
    type X
    type Y
    type Z

    fn xy {
      sig: X -> Y
      impl: formula("y = x + 1")
      cost: 1
      confidence: 1.0
    }

    fn yz {
      sig: Y -> Z
      impl: formula("z = y * 2")
      cost: 2
      confidence: 0.9
    }
    """

    catalog_dict = parse_dsl_string(dsl_content)
    cat = Catalog(catalog_dict)

    # カタログの内容を確認
    assert len(cat.types) == 3
    assert len(cat.funcs) == 2

    # 型合成を実行
    results = synthesize_backward(cat, src_type='X', goal_type='Z', max_cost=10)

    assert len(results) > 0, "Expected at least one path"
    cost, path = results[0]

    assert cost == 3.0, f"Expected cost 3.0, got {cost}"
    assert len(path) == 2, f"Expected 2 steps, got {len(path)}"
    assert path[0].id == 'xy'
    assert path[1].id == 'yz'

    # 信頼度の計算
    conf = 1.0
    for p in path:
        conf *= p.conf
    assert abs(conf - 0.9) < 0.001, f"Expected confidence 0.9, got {conf}"

    print("  パス: X → Y → Z")
    print(f"  コスト: {cost}")
    print(f"  信頼度: {conf}")
    print("✓ カタログ変換と型合成: 成功")
    return True

def test_nested_braces():
    """ネストした括弧の処理テスト"""
    print("\n" + "=" * 60)
    print("テスト3: ネストした括弧（SPARQL等）")
    print("=" * 60)

    dsl_content = """
    type Product
    type Energy

    fn getEnergy {
      sig: Product -> Energy
      impl: sparql("SELECT ?p ?e WHERE { ?p :hasEnergy ?e . FILTER(?e > 0) }")
      cost: 1
      confidence: 0.85
    }
    """

    parser = DSLParser()
    parser.parse(dsl_content)

    assert len(parser.functions) == 1
    fn = parser.functions[0]

    assert fn.id == 'getEnergy'
    assert fn.impl['kind'] == 'sparql'
    assert '{ ?p :hasEnergy ?e . FILTER(?e > 0) }' in fn.impl['query']
    assert fn.confidence == 0.85

    print("  関数: getEnergy")
    print(f"  SPARQL: {fn.impl['query']}")
    print(f"  信頼度: {fn.confidence}")
    print("✓ ネストした括弧の処理: 成功")
    return True

def test_inverse_functions():
    """逆関数のテスト"""
    print("\n" + "=" * 60)
    print("テスト4: 逆関数（inverse_of）")
    print("=" * 60)

    dsl_content = """
    type Fuel
    type Energy

    fn fuelToEnergy {
      sig: Fuel -> Energy
      impl: formula("e = f * density")
      cost: 1
      confidence: 0.95
    }

    fn energyToFuel {
      sig: Energy -> Fuel
      impl: formula("f = e / density")
      cost: 3
      confidence: 0.8
      inverse_of: fuelToEnergy
    }
    """

    parser = DSLParser()
    parser.parse(dsl_content)

    assert len(parser.functions) == 2

    f_to_e = next(f for f in parser.functions if f.id == 'fuelToEnergy')
    e_to_f = next(f for f in parser.functions if f.id == 'energyToFuel')

    assert f_to_e.inverse_of is None
    assert e_to_f.inverse_of == 'fuelToEnergy'
    assert e_to_f.cost == 3.0  # 逆関数は通常コストが高い
    assert e_to_f.confidence == 0.8  # 逆関数は信頼度が低い

    print("  順方向: Fuel → Energy (cost=1, conf=0.95)")
    print("  逆方向: Energy → Fuel (cost=3, conf=0.8, inverse)")
    print("✓ 逆関数の処理: 成功")
    return True

def test_cfp_example():
    """実際のCFP例のテスト"""
    print("\n" + "=" * 60)
    print("テスト5: CFP計算の実例")
    print("=" * 60)

    # catalog.dslを読み込む
    try:
        cat = Catalog.from_dsl('catalog.dsl')
    except FileNotFoundError:
        print("⚠ catalog.dsl が見つかりません。スキップします。")
        return True

    # Product -> CO2 のパスを探索
    results = synthesize_backward(cat, src_type='Product', goal_type='CO2', max_cost=50)

    assert len(results) > 0, "CFP計算のパスが見つかりません"

    cost, path = results[0]
    assert cost == 5.0, f"Expected cost 5.0, got {cost}"

    # 信頼度の計算
    conf = 1.0
    for p in path:
        conf *= p.conf

    expected_conf = 0.9 * 0.8 * 0.98  # 0.7056
    assert abs(conf - expected_conf) < 0.001, f"Expected confidence {expected_conf}, got {conf}"

    print("  パス: Product → Energy → Fuel → CO2")
    print(f"  コスト: {cost}")
    print(f"  信頼度: {conf:.4f}")
    print(f"  関数列: {' ∘ '.join([p.id for p in path])}")
    print("✓ CFP計算の実例: 成功")
    return True

def main():
    """すべてのテストを実行"""
    print("\n" + "=" * 60)
    print("DSL統合テストスイート")
    print("=" * 60)

    tests = [
        test_dsl_parsing,
        test_catalog_integration,
        test_nested_braces,
        test_inverse_functions,
        test_cfp_example,
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
            failed += 1

    print("\n" + "=" * 60)
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
