#!/usr/bin/env python3
# run_executable.py
"""
実行可能な型合成システム - 統合スクリプト

探索、実行、単位変換、Provenance生成をすべて統合したフルスタックの実行スクリプト
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

from synth_lib import Catalog, synthesize_backward, path_to_json
from executor import PathExecutor, ExecutionContext, create_mock_context
from unit_converter import UnitConverter, UnitAwareCatalog
from provenance import ProvenanceGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Type-Theoretic Ontology Synthesis System - Executable Version'
    )
    parser.add_argument('catalog', help='DSL or YAML catalog file')
    parser.add_argument('src_type', help='Source type')
    parser.add_argument('goal_type', help='Goal type')
    parser.add_argument('input_value', type=float, help='Input value')

    parser.add_argument('--max-cost', type=float, default=50,
                       help='Maximum cost for path search')
    parser.add_argument('--execute', action='store_true',
                       help='Execute the path (not just search)')
    parser.add_argument('--mock', action='store_true',
                       help='Use mock mode for execution')
    parser.add_argument('--sparql-endpoint', type=str,
                       help='SPARQL endpoint URL')
    parser.add_argument('--param', action='append', default=[],
                       help='Parameters in key=value format (can be used multiple times)')
    parser.add_argument('--provenance', action='store_true',
                       help='Generate provenance (PROV-O)')
    parser.add_argument('--prov-format', choices=['turtle', 'json'], default='turtle',
                       help='Provenance output format')
    parser.add_argument('--prov-output', type=str,
                       help='Provenance output file (default: stdout)')
    parser.add_argument('--unit-conversion', action='store_true',
                       help='Enable automatic unit conversion')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # パラメータをパース
    parameters = {}
    for param_str in args.param:
        if '=' in param_str:
            key, value = param_str.split('=', 1)
            # 数値に変換を試みる
            try:
                value = float(value)
            except ValueError:
                pass
            parameters[key.strip()] = value

    # デフォルトパラメータ
    default_params = {
        'emission_factor': 2.7,  # kg-CO2/kg-fuel
        'energy_density': 42e6,  # J/kg (gasoline)
        'efficiency': 0.35,
    }
    default_params.update(parameters)
    parameters = default_params

    if args.verbose:
        print(f"Loading catalog from {args.catalog}...", file=sys.stderr)

    # カタログを読み込み
    if args.catalog.endswith('.dsl'):
        cat = Catalog.from_dsl(args.catalog)
    else:
        cat = Catalog.from_yaml(args.catalog)

    if args.verbose:
        print(f"Catalog loaded: {len(cat.types)} types, {len(cat.funcs)} functions",
              file=sys.stderr)
        print(f"Searching for path: {args.src_type} -> {args.goal_type}",
              file=sys.stderr)

    # パスを探索
    results = synthesize_backward(cat, src_type=args.src_type,
                                 goal_type=args.goal_type,
                                 max_cost=args.max_cost)

    if not results:
        print(f"✗ No path found from {args.src_type} to {args.goal_type}",
              file=sys.stderr)
        return 1

    cost, path = results[0]

    if args.verbose:
        print(f"✓ Found path with cost {cost}", file=sys.stderr)
        print(f"  Functions: {' -> '.join([f.id for f in path])}",
              file=sys.stderr)

    # 単位変換の適用（オプション）
    if args.unit_conversion:
        if args.verbose:
            print("Applying unit conversions...", file=sys.stderr)
        unit_catalog = UnitAwareCatalog(cat)
        path = unit_catalog.augment_path_with_conversions(
            path, args.src_type, args.goal_type
        )
        if args.verbose:
            print(f"  Path after unit conversion: {' -> '.join([f.id for f in path])}",
                  file=sys.stderr)

    # 基本的な結果を出力（探索モード）
    output = {
        "goal": f"{args.src_type}->{args.goal_type}",
        "input_value": args.input_value,
        "path": {
            "cost": cost,
            "confidence": calculate_confidence(path),
            "steps": path_to_json(path),
            "proof": " ∘ ".join([p.id for p in path])
        }
    }

    # 実行モード
    if args.execute:
        if args.verbose:
            print(f"\nExecuting path with input value: {args.input_value}",
                  file=sys.stderr)

        # 実行コンテキストを作成
        context = ExecutionContext(
            parameters=parameters,
            sparql_endpoint=args.sparql_endpoint,
            mock_mode=args.mock,
            record_provenance=args.provenance
        )

        # パスを実行
        executor = PathExecutor()
        final_result, execution_steps = executor.execute_path(
            path, args.input_value, context
        )

        if args.verbose:
            print(f"✓ Execution completed", file=sys.stderr)
            print(f"  Final result: {final_result}", file=sys.stderr)

        # 実行結果を追加
        output["execution"] = {
            "final_result": final_result,
            "steps": [
                {
                    "step": i + 1,
                    "function": step.function_id,
                    "input": step.input_value,
                    "output": step.output_value,
                    "implementation": step.impl_kind
                }
                for i, step in enumerate(execution_steps)
            ],
            "parameters_used": parameters,
            "mock_mode": args.mock
        }

        # Provenance生成（オプション）
        if args.provenance:
            if args.verbose:
                print("Generating provenance...", file=sys.stderr)

            synthesis_id = str(uuid.uuid4())[:8]
            generator = ProvenanceGenerator()
            prov = generator.generate_synthesis_provenance(
                synthesis_id=synthesis_id,
                goal=f"{args.src_type}->{args.goal_type}",
                path=path,
                input_value=args.input_value,
                output_value=final_result,
                execution_steps=execution_steps,
                context=context
            )

            # Provenance出力
            if args.prov_format == 'turtle':
                prov_output = prov.to_turtle()
            else:
                prov_output = prov.to_json()

            if args.prov_output:
                with open(args.prov_output, 'w') as f:
                    f.write(prov_output)
                if args.verbose:
                    print(f"Provenance saved to {args.prov_output}",
                          file=sys.stderr)
            else:
                print("\n# Provenance:", file=sys.stderr)
                print(prov_output)

            output["provenance_file"] = args.prov_output or "stdout"

    # メイン結果をJSON出力
    print(json.dumps(output, indent=2, ensure_ascii=False))

    return 0


def calculate_confidence(path):
    """パスの信頼度を計算"""
    conf = 1.0
    for func in path:
        conf *= func.conf
    return round(conf, 6)


if __name__ == '__main__':
    sys.exit(main())
