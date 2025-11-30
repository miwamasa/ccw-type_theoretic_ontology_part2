# Product型ガイド

## 概要

**Product型**は、複数の型を1つの型として扱うための機能です。型理論における直積型（Product Type）に相当します。

多引数関数の完全なサポートに向けた**中間的な解決策**として実装されており、GHG Scope 1, 2, 3のような複数のデータソースを統合する場合に有用です。

## 実装状況

✅ **フェーズ1: Product型サポート** - 完了

- Product型の定義と型システムへの統合
- DSL構文のサポート (`type Name = A × B × C`)
- ビルトイン関数 (`builtin("product")`)
- Formula実行エンジンでのProduct型処理
- GHG Scope 1,2,3での実用例
- 包括的なテストスイート

## Product型の定義

### DSL構文

```dsl
# Product型の定義
type AllScopesEmissions = Scope1Emissions × Scope2Emissions × Scope3Emissions

# 代替構文（×が使えない環境）
type AllScopesEmissions = Scope1Emissions x Scope2Emissions x Scope3Emissions
```

### 構造

Product型は、複数の型のタプルとして内部的に表現されます：

```python
# 型定義
AllScopesEmissions = (Scope1Emissions, Scope2Emissions, Scope3Emissions)

# 値の例
allscopes_value = (1000.0, 1500.0, 800.0)
#                  ^^^^^^  ^^^^^^  ^^^^^^
#                  Scope1  Scope2  Scope3
```

## ビルトイン関数

### `builtin("product")`

複数の値を1つのProduct型の値として統合します。

**DSL定義例:**

```dsl
fn buildAllScopes {
  sig: Scope1Emissions -> AllScopesEmissions
  impl: builtin("product")
  cost: 0
  confidence: 1.0
}
```

**注意**: 現在の型システムでは単一入力しかサポートされていないため、このシグネチャは実際には複数の値を受け取ることができません。実用的には、各Scopeを個別に計算してから手動でProduct型を構築する必要があります。

### `builtin("sum")`

複数の値の合計を計算します（将来の拡張用）。

### `builtin("identity")`

恒等関数（値をそのまま返す）。

## Formula実行エンジンでのProduct型処理

Product型の値（タプル）は、Formula実行時に自動的に変数にバインドされます：

```dsl
fn aggregateAllScopes {
  sig: AllScopesEmissions -> TotalGHGEmissions
  impl: formula("total = scope1 + scope2 + scope3")
  cost: 1
  confidence: 1.0
}
```

**変数バインディング:**

入力値が `(1000.0, 1500.0, 800.0)` の場合：

```python
scope1 = 1000.0  # タプルの1番目の要素
scope2 = 1500.0  # タプルの2番目の要素
scope3 = 800.0   # タプルの3番目の要素
x1 = 1000.0      # 代替名
x2 = 1500.0
x3 = 800.0
```

これにより、Formula式で `scope1 + scope2 + scope3` のように記述できます。

## 使用例：GHG Scope 1, 2, 3の集約

### 問題設定

GHG（温室効果ガス）排出量は、3つのScopeに分類されます：

- **Scope 1**: 直接排出（燃料燃焼等）
- **Scope 2**: 間接排出（購入電力等）
- **Scope 3**: その他間接排出（サプライチェーン等）

**目標**: 3つのScopeの排出量を合計して、総排出量（TotalGHGEmissions）を計算する

### 従来のアプローチの問題

```dsl
fn aggregateScope2toTotal {
  sig: Scope2Emissions -> TotalGHGEmissions
  impl: formula("total = scope2")  # Scope2だけ！
  cost: 0.5
}
```

型充足アルゴリズムは `Facility -> TotalGHGEmissions` のパスを探すとき、**最もコストが低いパス**（Scope2経由）を選択してしまいます。

**結果**: Scope2だけの排出量がTotalとして返される（不正確）

### Product型を使った解決策

#### 1. Product型の定義

```dsl
# 3つのScopeを統合するProduct型
type AllScopesEmissions = Scope1Emissions × Scope2Emissions × Scope3Emissions
```

#### 2. 集約関数の定義

```dsl
fn aggregateAllScopes {
  sig: AllScopesEmissions -> TotalGHGEmissions
  impl: formula("total = scope1 + scope2 + scope3")
  cost: 1
  confidence: 1.0
}
```

#### 3. 使用方法

```python
from synth_lib import Catalog, synthesize_backward
from executor import PathExecutor, ExecutionContext

# カタログを読み込み
catalog = Catalog.from_dsl("ghg_scope123_product.dsl")

# AllScopes -> Total のパスを探索
results = synthesize_backward(catalog, "AllScopesEmissions", "TotalGHGEmissions")
cost, path = results[0]

# Product型の値を構築（手動で3つのScopeの値を用意）
allscopes_value = (1000.0, 1500.0, 800.0)  # (Scope1, Scope2, Scope3)

# パスを実行
executor = PathExecutor()
context = ExecutionContext(mock_mode=True)
final_value, steps = executor.execute_path(path, allscopes_value, context)

print(f"Total GHG Emissions: {final_value} kg-CO2")
# 出力: Total GHG Emissions: 3300.0 kg-CO2
```

## 実用的なワークフロー

現在の型システムの制限により、完全に自動化されたワークフローはまだサポートされていません。以下の手動ステップが必要です：

### ステップ1: 各Scopeの値を個別に計算

```python
# Scope1への変換パスを探索・実行
results1 = synthesize_backward(catalog, "Facility", "Scope1Emissions")
scope1_value = execute_path(results1[0][1], facility_data, context)

# Scope2への変換パスを探索・実行
results2 = synthesize_backward(catalog, "Facility", "Scope2Emissions")
scope2_value = execute_path(results2[0][1], facility_data, context)

# Scope3への変換パスを探索・実行
results3 = synthesize_backward(catalog, "Organization", "Scope3Emissions")
scope3_value = execute_path(results3[0][1], org_data, context)
```

### ステップ2: Product型を構築

```python
allscopes_value = (scope1_value, scope2_value, scope3_value)
```

### ステップ3: 集約を実行

```python
results_final = synthesize_backward(catalog, "AllScopesEmissions", "TotalGHGEmissions")
total_emissions = execute_path(results_final[0][1], allscopes_value, context)
```

**参考**: `demo_ghg_multipath.py` に完全な例があります。

## テストと検証

### テストスイートの実行

```bash
cd type_inhabitation_DSL
python3 test_product_type.py
```

### テスト内容

1. **Product型の定義のパース**: DSL構文が正しくパースされるか確認
2. **パス探索**: Product型を含むパスが正しく探索されるか確認
3. **実行**: Product型の値が正しく処理されるか確認
4. **集約**: Formula式でProduct型の各要素が正しくアクセスできるか確認
5. **比較**: 従来のアプローチとの比較

### 期待される結果

```
================================================================================
テスト結果サマリー
================================================================================
✓ 5/5 テストが成功

🎉 すべてのテストが成功しました！
```

## 制限事項と今後の展望

### 現在の制限

1. **単一入力の関数のみ**: 型システムは `A -> B` の形式しかサポートしていない
2. **手動での値の構築**: Product型の値を構築するには、各コンポーネントを個別に計算する必要がある
3. **型安全性の不完全**: Product型のコンポーネント数と実際の値の要素数の整合性チェックが不完全

### 将来の拡張

#### フェーズ2: 完全な多引数関数サポート（4-6日）

```dsl
fn aggregateAllScopes {
  sig: (Scope1Emissions, Scope2Emissions, Scope3Emissions) -> TotalGHGEmissions
  impl: formula("total = scope1 + scope2 + scope3")
  cost: 1
}
```

**必要な変更**:
- 探索アルゴリズムの拡張（複数の入力型への対応）
- 実行エンジンのDAG構築とトポロジカルソート
- 型チェックの強化

#### 代替案: ワークフロー記述言語（3-4日）

```yaml
workflow: calculate_total_ghg
steps:
  - id: scope1
    synthesize: {source: Facility, goal: Scope1Emissions}
  - id: scope2
    synthesize: {source: Facility, goal: Scope2Emissions}
  - id: scope3
    synthesize: {source: Organization, goal: Scope3Emissions}
  - id: total
    function: sum
    inputs: [scope1, scope2, scope3]
    output: TotalGHGEmissions
```

## まとめ

Product型は、多引数関数の完全なサポートに向けた**重要な第一歩**です：

✅ **達成したこと**:
- GHG集約問題の解決
- 型システムの拡張可能性の実証
- 実用的なワークフローの提供

🔜 **次のステップ**:
- フェーズ2: 完全な多引数関数サポート
- または、ワークフロー記述言語の導入

Product型により、複雑なデータ統合タスクを型安全に実行できるようになりました。
