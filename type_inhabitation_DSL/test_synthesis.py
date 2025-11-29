# test_synthesis.py
# 複数のテストケースで型合成システムの動作を検証
import yaml, json
from synth_lib import Catalog, synthesize_backward, path_to_json

def test_case(catalog, src, goal, max_cost=50, description=""):
    """単一のテストケースを実行"""
    print(f"\n{'='*60}")
    print(f"テスト: {description}")
    print(f"探索: {src} -> {goal}")
    print(f"{'='*60}")

    results = synthesize_backward(catalog, src_type=src, goal_type=goal, max_cost=max_cost)

    if not results:
        print(f"❌ パスが見つかりませんでした")
        return False

    print(f"✓ {len(results)}個のパスが見つかりました\n")

    for i, (cost, path) in enumerate(results[:3], 1):  # 上位3件のみ表示
        conf = 1.0
        for p in path:
            conf *= p.conf

        steps_str = " → ".join([p.dom for p in path] + [path[-1].cod])
        funcs_str = " ∘ ".join([p.id for p in path])

        print(f"パス {i}:")
        print(f"  型遷移: {steps_str}")
        print(f"  関数合成: {funcs_str}")
        print(f"  コスト: {cost}")
        print(f"  信頼度: {conf:.6f}")
        print()

    return True

def main():
    # カタログを読み込み
    catalog_path = "catalog.yaml"
    with open(catalog_path, "r", encoding="utf-8") as f:
        cat_dict = yaml.safe_load(f)
    cat = Catalog(cat_dict)

    print("="*60)
    print("型理論ベース オントロジー合成システム - 動作検証")
    print("="*60)

    # カタログ情報を表示
    print(f"\n📋 カタログ情報:")
    print(f"  型の数: {len(cat.types)}")
    print(f"  関数の数: {len(cat.funcs)}")
    print(f"  型: {', '.join(cat.types.keys())}")
    print(f"\n📝 関数一覧:")
    for f in cat.funcs:
        print(f"  - {f.id}: {f.dom} -> {f.cod} (cost={f.cost}, conf={f.conf})")

    # テストケース1: Product -> CO2 (メインの例題)
    test_case(cat, "Product", "CO2", description="CFP計算: Product -> CO2")

    # テストケース2: Product -> Energy (直接接続)
    test_case(cat, "Product", "Energy", description="エネルギー使用量: Product -> Energy")

    # テストケース3: Fuel -> CO2 (直接接続)
    test_case(cat, "Fuel", "CO2", description="燃料排出: Fuel -> CO2")

    # テストケース4: Fuel -> Energy (直接接続)
    test_case(cat, "Fuel", "Energy", description="燃料→エネルギー変換: Fuel -> Energy")

    # テストケース5: Energy -> CO2 (間接的)
    test_case(cat, "Energy", "CO2", description="エネルギー→CO2: Energy -> CO2")

    # テストケース6: Product -> Fuel (間接的)
    test_case(cat, "Product", "Fuel", description="製品→燃料推定: Product -> Fuel")

    print("\n" + "="*60)
    print("✓ すべてのテストケースが完了しました")
    print("="*60)

if __name__ == "__main__":
    main()
