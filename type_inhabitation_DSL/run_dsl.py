# run_dsl.py
"""
DSLファイルを使って型合成システムを実行

使用例:
  python run_dsl.py catalog.dsl Product CO2
"""

import json
import sys
from synth_lib import Catalog, synthesize_backward, path_to_json

def prod_confidence(path):
    """パスの信頼度を計算（積）"""
    if not path:
        return 1.0
    prod = 1.0
    for p in path:
        prod *= p.conf
    return prod

def main():
    if len(sys.argv) < 4:
        print("Usage: python run_dsl.py <catalog.dsl> <src_type> <goal_type> [max_cost]")
        print("\nExample:")
        print("  python run_dsl.py catalog.dsl Product CO2")
        print("  python run_dsl.py catalog.dsl Product CO2 10")
        sys.exit(1)

    dsl_file = sys.argv[1]
    src_type = sys.argv[2]
    goal_type = sys.argv[3]
    max_cost = int(sys.argv[4]) if len(sys.argv) > 4 else 50

    # DSLファイルからカタログを読み込み
    print(f"Loading catalog from {dsl_file}...", file=sys.stderr)
    cat = Catalog.from_dsl(dsl_file)

    print(f"Catalog loaded:", file=sys.stderr)
    print(f"  Types: {len(cat.types)}", file=sys.stderr)
    print(f"  Functions: {len(cat.funcs)}", file=sys.stderr)
    print(f"\nSearching for path: {src_type} -> {goal_type}", file=sys.stderr)
    print(f"Max cost: {max_cost}\n", file=sys.stderr)

    # 型合成を実行
    results = synthesize_backward(cat, src_type=src_type, goal_type=goal_type, max_cost=max_cost)

    # 結果をJSON形式で出力
    out = {
        "goal": f"{src_type}->{goal_type}",
        "plans": []
    }

    for cost, path in results:
        out["plans"].append({
            "cost": cost,
            "confidence_est": round(prod_confidence(path), 6),
            "steps": path_to_json(path),
            "proof": " ∘ ".join([p.id for p in path])
        })

    print(json.dumps(out, indent=2, ensure_ascii=False))

    # サマリーを stderr に出力
    if results:
        print(f"\n✓ Found {len(results)} path(s)", file=sys.stderr)
        best_cost, best_path = results[0]
        print(f"  Best path cost: {best_cost}", file=sys.stderr)
        print(f"  Best path confidence: {prod_confidence(best_path):.6f}", file=sys.stderr)
    else:
        print(f"\n✗ No path found from {src_type} to {goal_type}", file=sys.stderr)

if __name__ == "__main__":
    main()
