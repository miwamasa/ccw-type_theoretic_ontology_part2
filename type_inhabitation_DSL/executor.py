# executor.py
"""
型理論ベースオントロジー合成システム - 実行レイヤー

関数の実装（SPARQL/REST/Formula）を実際に実行し、
結果を生成します。
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid

# オプショナルな依存関係
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests library not found. REST API execution will not work.")

try:
    from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON
    HAS_SPARQL = True
except ImportError:
    HAS_SPARQL = False
    print("Warning: SPARQLWrapper not found. SPARQL execution will not work.")


@dataclass
class ExecutionContext:
    """実行コンテキスト - パラメータとデータソースを管理"""
    parameters: Dict[str, Any] = field(default_factory=dict)
    sparql_endpoint: Optional[str] = None
    mock_mode: bool = False
    record_provenance: bool = True
    base_uri: str = "http://example.org/"

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """パラメータを取得"""
        return self.parameters.get(name, default)


@dataclass
class ExecutionResult:
    """実行結果"""
    value: Any
    type_name: str
    unit: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class ExecutionStep:
    """実行ステップの記録（Provenance用）"""
    step_id: str
    function_id: str
    function_sig: str
    input_value: Any
    output_value: Any
    impl_kind: str
    impl_details: Dict[str, Any]
    timestamp: str
    parameters_used: Dict[str, Any] = field(default_factory=dict)
    data_sources: List[str] = field(default_factory=list)


class FormulaExecutor:
    """Formula実行エンジン"""

    def execute(self, formula_expr: str, input_value: Any,
                context: ExecutionContext) -> ExecutionResult:
        """数式を評価"""

        # 簡易的な数式パーサー（安全性のため限定的）
        # 実際の実装では、より厳密なパーサーを使用すべき

        # 入力値を変数としてバインド
        variables = {
            'input': input_value,
            'value': input_value,
        }

        # Product型（タプル）の場合、各要素を変数にバインド
        if isinstance(input_value, (tuple, list)):
            # タプルの要素をscope1, scope2, scope3として登録
            for i, val in enumerate(input_value):
                variables[f'scope{i+1}'] = val
                variables[f'x{i+1}'] = val  # x1, x2, x3としても登録
            # 互換性のため、xにも登録（単一値として扱う場合）
            if len(input_value) > 0:
                variables['x'] = input_value[0]
        else:
            variables['x'] = input_value

        # コンテキストからパラメータを取得
        variables.update(context.parameters)

        try:
            # 式を評価（安全性のため、制限された名前空間で）
            # 実際の実装では、より安全な評価方法を使用
            safe_dict = {
                '__builtins__': {},
                'abs': abs,
                'min': min,
                'max': max,
                'round': round,
            }
            safe_dict.update(variables)

            # 式から計算を抽出（例: "co2 = fuel_amount * emission_factor"）
            if '=' in formula_expr:
                lhs, rhs = formula_expr.split('=', 1)
                rhs = rhs.strip()

                # 変数名をマッピング
                # fuel_amount -> input, energy -> input など
                rhs = re.sub(r'\bfuel_amount\b', 'input', rhs)
                rhs = re.sub(r'\benergy\b', 'input', rhs)
                rhs = re.sub(r'\bfuel\b', 'input', rhs)

                result = eval(rhs, safe_dict)
            else:
                result = eval(formula_expr, safe_dict)

            return ExecutionResult(
                value=result,
                type_name="Number",
                metadata={
                    'formula': formula_expr,
                    'input': input_value,
                    'variables': variables
                }
            )
        except Exception as e:
            # エラーの場合、モック値を返す
            # Product型の場合は合計値を返す
            if isinstance(input_value, (tuple, list)):
                mock_value = sum(input_value) if input_value else 0
            else:
                mock_value = input_value * 1.5 if isinstance(input_value, (int, float)) else input_value

            return ExecutionResult(
                value=mock_value,
                type_name="Number",
                confidence=0.5,
                metadata={
                    'formula': formula_expr,
                    'error': str(e),
                    'mock': True
                }
            )


class SPARQLExecutor:
    """SPARQL実行エンジン"""

    def execute(self, query: str, input_value: Any,
                context: ExecutionContext) -> ExecutionResult:
        """SPARQLクエリを実行"""

        if context.mock_mode or not HAS_SPARQL or not context.sparql_endpoint:
            # モックモード: ダミーデータを返す
            return self._mock_execute(query, input_value, context)

        try:
            sparql = SPARQLWrapper(context.sparql_endpoint)

            # クエリ内のプレースホルダーを置換
            formatted_query = query.replace('{input}', str(input_value))

            sparql.setQuery(formatted_query)
            sparql.setReturnFormat(SPARQL_JSON)
            results = sparql.query().convert()

            # 結果を抽出（最初の結果を返す）
            if results and 'results' in results and 'bindings' in results['results']:
                bindings = results['results']['bindings']
                if bindings:
                    first_result = bindings[0]
                    # 最初の変数の値を取得
                    for var, value_dict in first_result.items():
                        return ExecutionResult(
                            value=value_dict.get('value'),
                            type_name="SPARQLResult",
                            metadata={
                                'query': query,
                                'endpoint': context.sparql_endpoint,
                                'full_results': bindings
                            }
                        )

            # 結果がない場合
            return ExecutionResult(
                value=None,
                type_name="SPARQLResult",
                confidence=0.0,
                metadata={'query': query, 'no_results': True}
            )

        except Exception as e:
            return self._mock_execute(query, input_value, context, error=str(e))

    def _mock_execute(self, query: str, input_value: Any,
                     context: ExecutionContext, error: str = None) -> ExecutionResult:
        """モック実行（テスト用）"""
        # 簡易的なモックデータ生成
        mock_value = input_value if input_value else 100.0

        return ExecutionResult(
            value=mock_value,
            type_name="SPARQLResult",
            confidence=0.7,
            metadata={
                'query': query,
                'mock': True,
                'error': error
            }
        )


class RESTExecutor:
    """REST API実行エンジン"""

    def execute(self, method: str, url: str, input_value: Any,
                context: ExecutionContext) -> ExecutionResult:
        """REST APIを呼び出し"""

        if context.mock_mode or not HAS_REQUESTS:
            return self._mock_execute(method, url, input_value, context)

        try:
            # URLのプレースホルダーを置換
            formatted_url = url.replace('{input}', str(input_value))
            formatted_url = formatted_url.replace('{id}', str(input_value))

            # リクエストを送信
            if method.upper() == 'GET':
                response = requests.get(formatted_url, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(formatted_url, json={'value': input_value}, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            # レスポンスをパース
            data = response.json()

            return ExecutionResult(
                value=data,
                type_name="RESTResult",
                metadata={
                    'method': method,
                    'url': formatted_url,
                    'status_code': response.status_code
                }
            )

        except Exception as e:
            return self._mock_execute(method, url, input_value, context, error=str(e))

    def _mock_execute(self, method: str, url: str, input_value: Any,
                     context: ExecutionContext, error: str = None) -> ExecutionResult:
        """モック実行"""
        mock_value = {'result': input_value * 1.2 if isinstance(input_value, (int, float)) else input_value}

        return ExecutionResult(
            value=mock_value,
            type_name="RESTResult",
            confidence=0.6,
            metadata={
                'method': method,
                'url': url,
                'mock': True,
                'error': error
            }
        )


class BuiltinExecutor:
    """ビルトイン関数の実行エンジン"""

    def execute(self, builtin_name: str, input_values: List[Any],
                context: ExecutionContext, catalog=None) -> ExecutionResult:
        """
        ビルトイン関数を実行

        Args:
            builtin_name: ビルトイン関数名 ("product", "sum", etc.)
            input_values: 入力値のリスト
            context: 実行コンテキスト
            catalog: カタログ（型情報取得用）

        Returns:
            実行結果
        """
        if builtin_name == "product":
            # Product型の構築
            # 入力値をタプルとして返す
            return ExecutionResult(
                value=tuple(input_values),
                type_name="Product",  # 実際の型名は呼び出し側で設定
                metadata={
                    'builtin': 'product',
                    'components': input_values
                }
            )

        elif builtin_name == "sum":
            # 合計を計算
            total = sum(input_values)
            return ExecutionResult(
                value=total,
                type_name="Number",
                metadata={
                    'builtin': 'sum',
                    'operands': input_values
                }
            )

        elif builtin_name == "identity":
            # 恒等関数
            if len(input_values) != 1:
                raise ValueError(f"identity requires exactly 1 input, got {len(input_values)}")
            return ExecutionResult(
                value=input_values[0],
                type_name="Any",
                metadata={'builtin': 'identity'}
            )

        else:
            raise ValueError(f"Unknown builtin function: {builtin_name}")


class PathExecutor:
    """型合成パスの実行エンジン"""

    def __init__(self):
        self.formula_executor = FormulaExecutor()
        self.sparql_executor = SPARQLExecutor()
        self.rest_executor = RESTExecutor()
        self.builtin_executor = BuiltinExecutor()
        self.execution_steps: List[ExecutionStep] = []

    def execute_path(self, path, input_value: Any,
                    context: ExecutionContext) -> Tuple[Any, List[ExecutionStep]]:
        """
        型合成パスを実行

        Args:
            path: 関数のリスト（Funcオブジェクト）
            input_value: 初期入力値
            context: 実行コンテキスト

        Returns:
            (最終結果, 実行ステップのリスト)
        """
        self.execution_steps = []
        current_value = input_value

        for func in path:
            # 関数を実行
            result = self._execute_function(func, current_value, context)

            # 実行ステップを記録
            step = ExecutionStep(
                step_id=str(uuid.uuid4()),
                function_id=func.id,
                function_sig=f"{func.dom} -> {func.cod}",
                input_value=current_value,
                output_value=result.value,
                impl_kind=func.impl.get('kind', 'unknown'),
                impl_details=func.impl,
                timestamp=result.timestamp,
                parameters_used=dict(context.parameters),
                data_sources=self._extract_data_sources(func, context)
            )
            self.execution_steps.append(step)

            # 次のステップの入力として使用
            current_value = result.value

        return current_value, self.execution_steps

    def _execute_function(self, func, input_value: Any,
                         context: ExecutionContext) -> ExecutionResult:
        """単一の関数を実行"""
        impl_kind = func.impl.get('kind', '')

        if impl_kind == 'formula':
            expr = func.impl.get('expr', '')
            return self.formula_executor.execute(expr, input_value, context)

        elif impl_kind == 'sparql':
            query = func.impl.get('query', '')
            return self.sparql_executor.execute(query, input_value, context)

        elif impl_kind == 'rest':
            method = func.impl.get('method', 'GET')
            url = func.impl.get('url', '')
            return self.rest_executor.execute(method, url, input_value, context)

        elif impl_kind == 'builtin':
            builtin_name = func.impl.get('name', '')
            # ビルトイン関数は input_value をリストとして受け取る
            # 単一の値の場合はリストに変換
            if isinstance(input_value, (list, tuple)):
                input_values = list(input_value)
            else:
                input_values = [input_value]

            result = self.builtin_executor.execute(builtin_name, input_values, context)
            # 型名を実際の関数の出力型に設定
            result.type_name = func.cod
            return result

        else:
            # 未知の実装タイプ: パススルー
            return ExecutionResult(
                value=input_value,
                type_name=func.cod,
                confidence=0.5,
                metadata={'impl_kind': impl_kind, 'passthrough': True}
            )

    def _extract_data_sources(self, func, context: ExecutionContext) -> List[str]:
        """データソースを抽出"""
        sources = []

        if func.impl.get('kind') == 'sparql' and context.sparql_endpoint:
            sources.append(context.sparql_endpoint)
        elif func.impl.get('kind') == 'rest':
            url = func.impl.get('url', '')
            if url:
                sources.append(url)

        return sources


def create_mock_context(**params) -> ExecutionContext:
    """モック実行コンテキストを作成（テスト用）"""
    return ExecutionContext(
        parameters={
            'emission_factor': 2.7,  # kg-CO2/kg-fuel
            'energy_density': 42e6,  # J/kg (gasoline)
            'efficiency': 0.35,
            **params
        },
        mock_mode=True,
        record_provenance=True
    )


# 使用例
if __name__ == '__main__':
    # テスト実行
    from synth_lib import Catalog, synthesize_backward

    # カタログを読み込み
    cat = Catalog.from_dsl('catalog.dsl')

    # パスを探索
    results = synthesize_backward(cat, src_type='Product', goal_type='CO2')

    if results:
        cost, path = results[0]
        print(f"Found path with cost {cost}")
        print(f"Functions: {' -> '.join([f.id for f in path])}")

        # パスを実行
        context = create_mock_context()
        executor = PathExecutor()

        # 入力: 製品のエネルギー使用量 = 360000 J (100 Wh)
        input_value = 360000

        final_result, steps = executor.execute_path(path, input_value, context)

        print(f"\nExecution Results:")
        print(f"Input: {input_value} J")
        print(f"Output: {final_result} kg-CO2")

        print(f"\nExecution Steps:")
        for i, step in enumerate(steps, 1):
            print(f"{i}. {step.function_id}: {step.input_value} -> {step.output_value}")
