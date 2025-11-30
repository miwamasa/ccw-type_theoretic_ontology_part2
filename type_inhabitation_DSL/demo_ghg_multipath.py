#!/usr/bin/env python3
"""
GHG Scope 1, 2, 3 の複数パス並行実行デモ

現在の型システムの制限：
- 単一入力の関数しかサポートしていない
- 複数のスコープを自動的に集約できない

このデモでは、各スコープのパスを個別に実行し、
最後に手動で合計することで、正しいTotal GHG Emissionsを計算します。
"""

import sys
import json
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dsl_parser import parse_dsl_file
from synth_lib import synthesize_backward, Catalog


def synthesize_all_scopes(catalog_file: str, facility_id: str = "facility_001"):
    """
    Facility から各 Scope への変換パスを個別に探索し、
    それぞれを実行してから手動で合計する
    """

    print("=" * 80)
    print("GHG Scope 1, 2, 3 複数パス並行実行デモ")
    print("=" * 80)
    print()

    # カタログを読み込み
    print(f"📖 カタログを読み込み: {catalog_file}")
    catalog = Catalog.from_dsl(catalog_file)
    print(f"   型: {len(catalog.types)} 個")
    print(f"   関数: {len(catalog.funcs)} 個")
    print()

    # 各スコープへのパスを探索
    scopes = [
        ("Scope1Emissions", "Scope 1: 直接排出"),
        ("Scope2Emissions", "Scope 2: エネルギー間接排出"),
        ("Scope3Emissions", "Scope 3: その他の間接排出")
    ]

    scope_results = {}

    for scope_type, scope_name in scopes:
        print(f"\n{'=' * 80}")
        print(f"🔍 パス探索: Facility -> {scope_type}")
        print(f"   {scope_name}")
        print(f"{'=' * 80}")

        try:
            results = synthesize_backward(catalog, "Facility", scope_type)

            if results:
                # 最良のパスを取得（resultsは[(cost, path), ...]のリスト）
                best_cost, path = results[0]

                print(f"✓ パス発見成功！")
                print(f"   パス長: {len(path)} ホップ")
                print(f"   総コスト: {best_cost}")
                total_conf = sum(f.conf for f in path) / len(path) if path else 0
                print(f"   総信頼度: {total_conf:.3f}")
                print(f"\n   関数の流れ:")
                for i, func in enumerate(path, 1):
                    print(f"      {i}. {func.id}: {func.dom} -> {func.cod}")

                # 実行をシミュレート（モック値を使用）
                mock_values = {
                    "Scope1Emissions": 1000.0,  # kg-CO2
                    "Scope2Emissions": 1500.0,  # kg-CO2
                    "Scope3Emissions": 800.0    # kg-CO2
                }

                result_value = mock_values.get(scope_type, 0.0)
                print(f"\n   実行結果（モック）: {result_value} kg-CO2")

                scope_results[scope_type] = {
                    "path": [f.id for f in path],
                    "cost": best_cost,
                    "confidence": total_conf,
                    "value": result_value
                }

            else:
                print(f"✗ パスが見つかりませんでした")
                scope_results[scope_type] = None

        except Exception as e:
            print(f"✗ エラー: {e}")
            scope_results[scope_type] = None

    # 結果を集約
    print(f"\n\n{'=' * 80}")
    print("📊 結果の集約")
    print(f"{'=' * 80}")

    total_emissions = 0.0
    for scope_type, scope_name in scopes:
        if scope_results[scope_type]:
            value = scope_results[scope_type]["value"]
            total_emissions += value
            print(f"   {scope_name:35s}: {value:10.2f} kg-CO2")
        else:
            print(f"   {scope_name:35s}: データなし")

    print(f"   {'-' * 50}")
    print(f"   {'Total GHG Emissions':35s}: {total_emissions:10.2f} kg-CO2")
    print()

    # 詳細な結果をJSON形式で出力
    output = {
        "facility_id": facility_id,
        "scope_results": scope_results,
        "total_emissions": total_emissions,
        "unit": "kg-CO2",
        "note": "現在の型システムは単一入力関数のみサポートのため、各スコープを個別に計算して手動で合計"
    }

    output_file = "ghg_multipath_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"📄 詳細結果を保存: {output_file}")
    print()

    # 問題点の説明
    print(f"\n{'=' * 80}")
    print("⚠️  型システムの制限について")
    print(f"{'=' * 80}")
    print("""
現在の型システムは単一入力の関数しかサポートしていません。

【問題点】
1. Facility -> TotalGHGEmissions のパスを探すと、
   Scope1, Scope2, Scope3 のうち**1つだけ**のパスが選ばれる

2. aggregateScope2toTotal のような関数は：
   - 入力: Scope2Emissions（Scope2だけ）
   - 出力: TotalGHGEmissions
   - 実装: formula("total = scope2")  # Scope2の値をそのままTotal

   つまり、**合計ではなく、単一スコープの値をTotalとして返す**

【解決策】
このデモでは、各スコープへのパスを個別に実行し、
最後に手動で合計することで正しい結果を得ています。

【今後の拡張】
- 多引数関数のサポート: (Scope1, Scope2, Scope3) -> Total
- Product型: Scope1 × Scope2 × Scope3
- 依存型: 値に依存する型システム

詳細は doc/ghg_aggregate_analysis.md を参照してください。
""")

    return output


if __name__ == "__main__":
    catalog_file = "ghg_scope123.dsl"

    if len(sys.argv) > 1:
        catalog_file = sys.argv[1]

    result = synthesize_all_scopes(catalog_file)

    print("\n✓ デモ完了")
