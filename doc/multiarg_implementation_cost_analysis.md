# 多引数関数サポートの実装コスト分析

## エグゼクティブサマリー

**実装コスト**: 中程度（3-5日の開発時間）

**複雑度**: 中程度
- コアアルゴリズムの大幅な変更が必要
- 後方互換性の維持が課題
- テストケースの追加が必要

**推奨アプローチ**: 段階的実装（フェーズ1: Product型、フェーズ2: 完全な多引数）

---

## 影響範囲の詳細分析

### 1. **型システムとデータ構造** (synth_lib.py: 103行)

#### 現在の実装
```python
@dataclass
class Func:
    id: str
    dom: str      # 単一の型名（文字列）
    cod: str      # 単一の型名（文字列）
    cost: float
    conf: float
    impl: dict
```

#### 必要な変更
```python
@dataclass
class Func:
    id: str
    dom: list[str]  # 複数の型名（リスト） ← 変更
    cod: str        # 単一の型名（文字列）
    cost: float
    conf: float
    impl: dict

    @property
    def arity(self) -> int:
        """引数の個数を返す"""
        return len(self.dom)
```

**変更箇所**:
- `Func`クラスの定義: 5-10行
- `Catalog.__init__`のインデックス構築: 15-20行
- 後方互換性のための変換ロジック: 10-15行

**小計**: 約30-45行の変更

---

### 2. **DSL構文とパーサー** (dsl_parser.py: 257行)

#### 現在の構文
```dsl
fn energyToEmissions {
  sig: EnergyConsumption -> kg-CO2
  ...
}
```

#### 新しい構文
```dsl
fn aggregateAllScopes {
  sig: (Scope1Emissions, Scope2Emissions, Scope3Emissions) -> TotalGHGEmissions
  ...
}

# 後方互換性のため、単一引数も許可
fn energyToEmissions {
  sig: EnergyConsumption -> kg-CO2  # これも有効
  ...
}
```

#### 必要な変更

**パース処理**:
```python
def parse_function_signature(sig_str: str) -> tuple[list[str], str]:
    """
    関数シグネチャをパースする

    例:
    - "A -> B" → (["A"], "B")
    - "(A, B, C) -> D" → (["A", "B", "C"], "D")
    """
    sig_str = sig_str.strip()

    if '->' not in sig_str:
        raise ValueError(f"Invalid signature: {sig_str}")

    left, right = sig_str.split('->', 1)
    left = left.strip()
    right = right.strip()

    # 複数引数のパース
    if left.startswith('(') and left.endswith(')'):
        # (A, B, C) 形式
        args_str = left[1:-1]
        domains = [arg.strip() for arg in args_str.split(',')]
    else:
        # 単一引数
        domains = [left]

    return domains, right
```

**変更箇所**:
- シグネチャパース関数の追加: 30-40行
- 既存のパース処理の修正: 10-15行
- テストケースの追加: 50-60行

**小計**: 約90-115行の変更・追加

---

### 3. **探索アルゴリズム** (synth_lib.py: 103行)

#### 現在の実装（後方探索）
```python
def synthesize_backward(catalog, src_type, goal_type):
    # ゴール型から開始
    pq = [(0.0, 0.0, counter, goal_type, [])]

    while pq:
        _, cum_cost, _, cur_type, path = heappop(pq)

        if cur_type == src_type:
            return path  # 成功

        # cur_type を返す関数を探す
        for f in catalog.funcs_returning(cur_type):
            # f.dom に進む
            next_type = f.dom  # 単一の型
            new_path = [f] + path
            heappush(pq, (..., next_type, new_path))
```

#### 多引数対応の実装

**課題**: 複数の入力型をどのように探索するか？

**アプローチ1**: 状態空間の拡張
```python
def synthesize_backward_multiarg(catalog, sources: dict[str, any], goal_type):
    """
    sources: {"type1": value1, "type2": value2, ...}
    利用可能な型とその値のマッピング
    """
    # 状態: (cost, current_type, path, required_types)
    # required_types: まだ満たされていない入力型の集合

    pq = [(0.0, goal_type, [], set())]

    while pq:
        cum_cost, cur_type, path, required = heappop(pq)

        # 全ての required が sources で満たされているかチェック
        if cur_type == goal_type and required.issubset(sources.keys()):
            return path

        for f in catalog.funcs_returning(cur_type):
            # f.dom は list[str]
            new_required = required.union(set(f.dom))
            new_path = [f] + path

            # 各入力型に対して再帰的に探索
            for dom_type in f.dom:
                heappush(pq, (cum_cost + f.cost, dom_type, new_path, new_required))
```

**複雑度の増加**:
- 状態空間が指数的に増大する可能性
- 部分的な型の充足を追跡する必要
- 循環依存の検出が複雑化

**変更箇所**:
- コアアルゴリズムの書き換え: 80-120行
- ヘルパー関数の追加: 30-40行
- 最適化ロジック: 40-60行

**小計**: 約150-220行の新規実装

---

### 4. **実行エンジン** (executor.py: 402行)

#### 現在の実装
```python
def execute_path(self, path, input_value):
    """パスを順次実行"""
    current_value = input_value

    for func in path:
        # func.impl に基づいて実行
        current_value = self.execute_function(func, current_value)

    return current_value

def execute_function(self, func, input_value):
    """単一の関数を実行（入力は1つ）"""
    if func.impl['type'] == 'formula':
        return eval_formula(func.impl['expr'], x=input_value)
    elif func.impl['type'] == 'sparql':
        return query_sparql(func.impl, input_value)
    # ...
```

#### 多引数対応の実装
```python
def execute_path(self, path, inputs: dict[str, any]):
    """
    パスを実行（複数の入力に対応）

    inputs: {"Scope1Emissions": 1000.0, "Scope2Emissions": 1500.0, ...}
    """
    # 依存関係グラフを構築
    dag = self.build_execution_dag(path)

    # トポロジカルソートして実行順序を決定
    execution_order = topological_sort(dag)

    # 各関数を実行
    values = inputs.copy()
    for func in execution_order:
        # 入力値を収集
        input_vals = [values[dom] for dom in func.dom]

        # 関数を実行
        result = self.execute_function(func, input_vals)
        values[func.cod] = result

    return values

def execute_function(self, func, input_values: list[any]):
    """
    複数の入力を持つ関数を実行

    input_values: [value1, value2, value3, ...]
    """
    if func.impl['type'] == 'formula':
        # 複数の変数を formula に渡す
        var_names = ['x1', 'x2', 'x3', ...]  # または明示的な名前
        var_dict = dict(zip(var_names, input_values))
        return eval_formula(func.impl['expr'], **var_dict)
    # ...
```

**新機能**:
- 依存関係グラフ (DAG) の構築
- トポロジカルソート
- 複数入力値の管理
- 実行順序の最適化

**変更箇所**:
- DAG構築ロジック: 60-80行
- トポロジカルソート: 30-40行
- 実行ロジックの修正: 50-70行
- Formula評価の拡張: 30-40行

**小計**: 約170-230行の変更・追加

---

### 5. **テストとドキュメント**

#### テストケース
- 単一引数関数の後方互換性テスト: 30-50行
- 2引数関数のテスト: 40-60行
- 3引数以上のテスト: 40-60行
- GHG Scope 1,2,3の統合テスト: 80-100行
- エッジケースのテスト: 60-80行

**小計**: 約250-350行のテストコード

#### ドキュメント
- DSL構文リファレンスの更新: 2-3時間
- 実装ガイドの作成: 3-4時間
- サンプルコードの作成: 2-3時間
- マイグレーションガイド: 2-3時間

**小計**: 約9-13時間のドキュメント作業

---

## 実装コストのまとめ

### コード変更量（行数）

| コンポーネント | 変更行数 | 新規行数 | 合計 |
|------------|---------|---------|------|
| 型システム (synth_lib.py) | 30-45 | 0 | 30-45 |
| DSLパーサー (dsl_parser.py) | 10-15 | 80-100 | 90-115 |
| 探索アルゴリズム (synth_lib.py) | 80-120 | 70-100 | 150-220 |
| 実行エンジン (executor.py) | 50-70 | 120-160 | 170-230 |
| テストコード | 0 | 250-350 | 250-350 |
| **合計** | **170-250** | **520-710** | **690-960** |

### 開発時間の見積もり

| タスク | 時間（人日） | 備考 |
|--------|------------|------|
| **フェーズ1: 設計** | 1-2日 | データ構造の詳細設計、API設計 |
| **フェーズ2: 実装** | | |
| - 型システムとパーサー | 1日 | 比較的単純 |
| - 探索アルゴリズム | 2-3日 | **最も複雑** |
| - 実行エンジン | 1-2日 | DAG構築とトポロジカルソート |
| **フェーズ3: テスト** | 1-2日 | 単体・統合テスト |
| **フェーズ4: ドキュメント** | 0.5-1日 | ユーザーガイド更新 |
| **合計** | **6.5-11日** | リスクバッファ含む |

### リスクと課題

#### 高リスク
1. **探索アルゴリズムの複雑化**
   - 状態空間の爆発
   - 性能劣化の可能性
   - 複雑なデバッグ

2. **後方互換性の維持**
   - 既存のDSLファイルが動作し続ける必要
   - マイグレーションパスの提供

#### 中リスク
1. **実行エンジンのDAG構築**
   - 循環依存の検出
   - エラーハンドリングの複雑化

2. **テストカバレッジ**
   - 多様な引数パターンのテスト
   - エッジケースの洗い出し

---

## 段階的実装アプローチ（推奨）

### **フェーズ1: Product型のサポート** (2-3日)

より簡単なアプローチとして、まず**Product型**を導入：

```dsl
# Product型の定義
type Scope123 = Scope1Emissions × Scope2Emissions × Scope3Emissions

# Product型を使った関数
fn aggregateAllScopes {
  sig: Scope123 -> TotalGHGEmissions
  impl: formula("total = scope1 + scope2 + scope3")
  ...
}

# Product型を構築する関数
fn buildScope123 {
  sig: (Scope1Emissions, Scope2Emissions, Scope3Emissions) -> Scope123
  impl: builtin("product")  # ビルトイン関数
  ...
}
```

**利点**:
- 既存の単一引数関数の枠組みを維持
- 探索アルゴリズムの大幅な変更不要
- 段階的な移行が可能

**実装コスト**: 2-3日

### **フェーズ2: 完全な多引数関数** (4-6日)

フェーズ1の経験を活かして、完全な多引数関数を実装：

```dsl
fn aggregateAllScopes {
  sig: (Scope1Emissions, Scope2Emissions, Scope3Emissions) -> TotalGHGEmissions
  impl: formula("total = scope1 + scope2 + scope3")
  ...
}
```

**実装コスト**: 4-6日

---

## 代替アプローチ: ワークフロー言語

多引数関数の代わりに、**ワークフロー記述言語**を導入する選択肢もあります：

```yaml
workflow: calculate_total_ghg
inputs:
  facility: Facility

steps:
  - id: scope1
    synthesize:
      source: facility
      goal: Scope1Emissions

  - id: scope2
    synthesize:
      source: facility
      goal: Scope2Emissions

  - id: scope3
    synthesize:
      source: organization
      goal: Scope3Emissions

  - id: total
    function: sum
    inputs: [scope1.result, scope2.result, scope3.result]
    output: TotalGHGEmissions
```

**利点**:
- 型システムの変更不要
- より柔軟なワークフロー記述
- デバッグが容易

**実装コスト**: 3-4日

---

## 推奨事項

### 短期（1-2週間）
**Product型のサポート** (フェーズ1)を実装
- 実装コスト: 2-3日
- リスク: 低
- 即座にGHG問題を解決可能

### 中期（1-2ヶ月）
**ワークフロー言語**の導入を検討
- より柔軟で保守性が高い
- 型システムの複雑化を避けられる

### 長期（3-6ヶ月）
研究成果として**完全な多引数関数サポート**を実装
- 学術的価値が高い
- より優雅な解決策
- 他のプロジェクトへの応用可能性

---

## 結論

**質問への回答**: 多引数関数のサポートには**3-5日**（段階的アプローチなら2-3日から開始可能）

**推奨**: まず**Product型**を2-3日で実装し、その後、必要に応じて完全な多引数関数やワークフロー言語に拡張する段階的アプローチを採用する。

これにより：
- 短期的にGHG集約問題を解決
- リスクを最小化
- 将来の拡張に向けた基盤を構築
