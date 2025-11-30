#!/usr/bin/env python3
# test_ghg_aggregate.py
"""
GHG Scope 1, 2, 3 シナリオのテスト
集約関数が型合成にどのように影響するかを分析
"""

import sys
from synth_lib import Catalog, synthesize_backward

def print_separator():
    print("=" * 70)

def print_path_details(results, scenario_name):
    """パスの詳細を表示"""
    print(f"\n{scenario_name}")
    print_separator()

    if not results:
        print("✗ パスが見つかりませんでした")
        return

    print(f"✓ {len(results)} 個のパスが見つかりました\n")

    for i, (cost, path) in enumerate(results[:5], 1):  # 上位5つ
        print(f"パス {i}:")
        print(f"  コスト: {cost}")
        print(f"  信頼度: {calculate_confidence(path):.4f}")
        print(f"  ステップ数: {len(path)}")
        print(f"  関数列:")
        for j, func in enumerate(path, 1):
            aggregate_marker = " [AGGREGATE]" if is_aggregate_function(func) else ""
            print(f"    {j}. {func.id}: {func.dom} -> {func.cod}{aggregate_marker}")
        print()

def calculate_confidence(path):
    """パスの信頼度を計算"""
    conf = 1.0
    for func in path:
        conf *= func.conf
    return conf

def is_aggregate_function(func):
    """関数が集約関数かどうかを判定"""
    aggregate_keywords = ['aggregate', 'sum', 'total', 'combine']
    return any(keyword in func.id.lower() for keyword in aggregate_keywords)

def count_aggregate_functions(path):
    """パス内の集約関数の数をカウント"""
    return sum(1 for func in path if is_aggregate_function(func))

def analyze_aggregate_impact(cat):
    """集約関数の影響を分析"""
    print("\n")
    print_separator()
    print("集約関数の影響分析")
    print_separator()

    # 集約関数のリスト
    aggregate_funcs = [f for f in cat.funcs if is_aggregate_function(f)]
    print(f"\n集約関数の数: {len(aggregate_funcs)}")
    print("集約関数:")
    for func in aggregate_funcs:
        print(f"  - {func.id}: {func.dom} -> {func.cod} (cost={func.cost}, conf={func.conf})")

    return len(aggregate_funcs)

def main():
    print("\nGHG Scope 1, 2, 3 レポート作成シナリオ")
    print_separator()

    # カタログを読み込み
    print("\nカタログを読み込み中...")
    cat = Catalog.from_dsl('ghg_scope123.dsl')
    print(f"✓ カタログ読み込み完了: {len(cat.types)} types, {len(cat.funcs)} functions")

    # 集約関数の分析
    num_aggregates = analyze_aggregate_impact(cat)

    # テストシナリオ
    scenarios = [
        # Scope 1: 直接排出
        {
            'name': 'シナリオ 1: Facility -> Scope1Emissions (直接排出)',
            'src': 'Facility',
            'goal': 'Scope1Emissions',
            'description': '施設からScope1排出量を計算（燃料使用+プロセス排出を集約）'
        },
        # Scope 2: エネルギー間接排出
        {
            'name': 'シナリオ 2: Facility -> Scope2Emissions (エネルギー間接排出)',
            'src': 'Facility',
            'goal': 'Scope2Emissions',
            'description': '施設からScope2排出量を計算（電力+熱）'
        },
        # Scope 3: その他の間接排出
        {
            'name': 'シナリオ 3: Organization -> Scope3Emissions (その他間接排出)',
            'src': 'Organization',
            'goal': 'Scope3Emissions',
            'description': '組織からScope3排出量を計算（輸送+通勤+出張）'
        },
        # Total: 全体の集約
        {
            'name': 'シナリオ 4: Organization -> TotalGHGEmissions (総排出量)',
            'src': 'Organization',
            'goal': 'TotalGHGEmissions',
            'description': '組織から総GHG排出量を計算（全Scopeを集約）'
        },
        # 個別ソースから総排出量まで
        {
            'name': 'シナリオ 5: Facility -> TotalGHGEmissions',
            'src': 'Facility',
            'goal': 'TotalGHGEmissions',
            'description': '施設から総排出量まで（複数の集約が必要）'
        },
        # 中間データからScope排出量
        {
            'name': 'シナリオ 6: FuelUsage -> Scope1Emissions',
            'src': 'FuelUsage',
            'goal': 'Scope1Emissions',
            'description': '燃料使用量からScope1排出量を計算'
        },
        {
            'name': 'シナリオ 7: PurchasedElectricity -> Scope2Emissions',
            'src': 'PurchasedElectricity',
            'goal': 'Scope2Emissions',
            'description': '電力使用量からScope2排出量を計算'
        },
        {
            'name': 'シナリオ 8: UpstreamTransport -> Scope3Emissions',
            'src': 'UpstreamTransport',
            'goal': 'Scope3Emissions',
            'description': '上流輸送からScope3排出量を計算'
        },
    ]

    # 各シナリオを実行
    all_results = {}
    for scenario in scenarios:
        results = synthesize_backward(
            cat,
            src_type=scenario['src'],
            goal_type=scenario['goal'],
            max_cost=50
        )
        all_results[scenario['name']] = results
        print_path_details(results, scenario['name'])

    # 統計分析
    print("\n")
    print_separator()
    print("統計分析: 集約関数の影響")
    print_separator()

    total_scenarios = len(scenarios)
    scenarios_with_paths = sum(1 for r in all_results.values() if r)
    scenarios_without_paths = total_scenarios - scenarios_with_paths

    print(f"\n総シナリオ数: {total_scenarios}")
    print(f"パスが見つかったシナリオ: {scenarios_with_paths}")
    print(f"パスが見つからなかったシナリオ: {scenarios_without_paths}")

    # 集約関数を含むパスの統計
    paths_with_aggregates = 0
    paths_without_aggregates = 0
    total_aggregate_count = 0

    for scenario_name, results in all_results.items():
        if results:
            cost, path = results[0]  # 最適パス
            num_agg = count_aggregate_functions(path)
            total_aggregate_count += num_agg
            if num_agg > 0:
                paths_with_aggregates += 1
            else:
                paths_without_aggregates += 1

    print(f"\n集約関数を含む最適パス: {paths_with_aggregates}")
    print(f"集約関数を含まない最適パス: {paths_without_aggregates}")
    print(f"最適パスに含まれる集約関数の総数: {total_aggregate_count}")

    # コストと信頼度の分析
    if all_results:
        print("\n最適パスのコストと信頼度:")
        for scenario_name, results in all_results.items():
            if results:
                cost, path = results[0]
                conf = calculate_confidence(path)
                num_agg = count_aggregate_functions(path)
                print(f"  {scenario_name[:50]:50s} | Cost: {cost:5.1f} | Conf: {conf:.4f} | Agg: {num_agg}")

    # 結論
    print("\n")
    print_separator()
    print("結論: 集約関数が型合成に与える影響")
    print_separator()
    print("""
1. パス発見への影響:
   - 集約関数は通常の関数と同様に型合成に統合される
   - 集約の有無はパスの発見可能性に直接影響しない

2. コストへの影響:
   - 集約関数のコストは他の関数と同様に累積される
   - 複数の入力を集約する場合でも、単一関数として扱われる

3. 信頼度への影響:
   - 集約関数の信頼度は経路全体の信頼度に乗算される
   - 集約関数が多いほど、信頼度が低下する可能性がある

4. 型システムへの影響:
   - 集約関数は型の変換として表現される (e.g., DirectFuelCombustion -> Scope1Emissions)
   - 実際には複数の入力が必要だが、型システムでは単一の型変換として扱われる
   - これは型理論の制限であり、将来的には依存型や多引数関数のサポートが必要
""")

    return 0

if __name__ == '__main__':
    sys.exit(main())
