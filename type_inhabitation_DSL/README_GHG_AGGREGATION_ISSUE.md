# GHG Scope 1, 2, 3 集約の問題と解決策

## 問題の概要

**ご指摘の通り、`Facility -> TotalGHGEmissions` のパス探索では、Scope2だけの履歴しか残りません。**

これは**型システムの根本的な制限**によるものです。

## 問題の詳細

### 1. 単一入力関数しかサポートしていない

現在の型システムでは、**単一入力の関数**（`A -> B`）しかサポートしていません。

```dsl
fn electricityToEmissions {
  sig: PurchasedElectricity -> Scope2Emissions  # 単一入力
  impl: formula("co2 = electricity * grid_emission_factor")
  ...
}
```

### 2. 集約関数が「集約」していない

`ghg_scope123.dsl` (155-174行目) の集約関数を見ると：

```dsl
fn aggregateScope1toTotal {
  sig: Scope1Emissions -> TotalGHGEmissions
  impl: formula("total = scope1")  # Scope1だけ！
  cost: 0.5
  confidence: 1.0
}

fn aggregateScope2toTotal {
  sig: Scope2Emissions -> TotalGHGEmissions
  impl: formula("total = scope2")  # Scope2だけ！
  cost: 0.5
  confidence: 1.0
}

fn aggregateScope3toTotal {
  sig: Scope3Emissions -> TotalGHGEmissions
  impl: formula("total = scope3")  # Scope3だけ！
  cost: 0.5
  confidence: 1.0
}
```

各関数は**単一のスコープ**を受け取り、その値を**そのまま** `TotalGHGEmissions` として返します。

**合計していません！**

### 3. 探索アルゴリズムの挙動

型充足アルゴリズムは `Facility -> TotalGHGEmissions` のパスを探すとき、以下の3つのパスから**コストが最小のもの**を選択します：

1. **Facility → Scope1Emissions → TotalGHGEmissions** (コスト: 2.5)
2. **Facility → Scope2Emissions → TotalGHGEmissions** (コスト: 2.0) ← **これが選ばれる**
3. Facility → Scope3Emissions → TotalGHGEmissions (パスなし※)

※ Scope3はFacilityからの直接パスが存在しない

結果：**Scope2だけの排出量が Total として返される**

## 実証デモ

`demo_ghg_multipath.py` を実行すると、問題が明確に示されます：

```bash
python3 demo_ghg_multipath.py
```

### デモの出力（抜粋）

```
================================================================================
🔍 パス探索: Facility -> Scope1Emissions
================================================================================
✓ パス発見成功！
   パス長: 3 ホップ
   総コスト: 3.0
   実行結果（モック）: 1000.0 kg-CO2

================================================================================
🔍 パス探索: Facility -> Scope2Emissions
================================================================================
✓ パス発見成功！
   パス長: 2 ホップ
   総コスト: 2.0
   実行結果（モック）: 1500.0 kg-CO2

================================================================================
📊 結果の集約
================================================================================
   Scope 1: 直接排出                      :    1000.00 kg-CO2
   Scope 2: エネルギー間接排出                 :    1500.00 kg-CO2
   Scope 3: その他の間接排出                  : データなし
   --------------------------------------------------
   Total GHG Emissions                :    2500.00 kg-CO2  ← 手動で合計
```

デモでは、各スコープへのパスを**個別に探索・実行**し、最後に**手動で合計**することで、正しいTotal GHG Emissionsを計算しています。

## 根本原因

現在の型システムの制限：

- **単一入力関数のみ**: `A -> B` の形式のみサポート
- **必要なもの**: `(A, B, C) -> D` のような**多引数関数**

本来必要な集約関数：

```
aggregateAllScopes: (Scope1Emissions, Scope2Emissions, Scope3Emissions) -> TotalGHGEmissions
```

これは現在の型システムでは表現できません。

## 解決策

### 1. **即座の対応**: 複数パスの並行実行と手動集約

`demo_ghg_multipath.py` のアプローチ：

1. 各スコープへのパスを個別に探索
2. それぞれを実行
3. 結果を手動で合計

**長所**:
- 現在のシステムで動作する
- 正しい結果が得られる

**短所**:
- 手動での集約が必要
- 型充足問題として定式化できていない

### 2. **中期的対応**: ワークフロー言語への拡張

パイプライン記述言語を導入：

```yaml
workflow: calculate_total_ghg
steps:
  - id: scope1
    goal: Facility -> Scope1Emissions

  - id: scope2
    goal: Facility -> Scope2Emissions

  - id: scope3
    goal: Organization -> Scope3Emissions

  - id: aggregate
    function: sum
    inputs: [scope1, scope2, scope3]
    output: TotalGHGEmissions
```

### 3. **長期的対応**: 型システムの拡張

#### 3a. 多引数関数のサポート

```dsl
fn aggregateAllScopes {
  sig: (Scope1Emissions, Scope2Emissions, Scope3Emissions) -> TotalGHGEmissions
  impl: formula("total = scope1 + scope2 + scope3")
  cost: 1
  confidence: 1.0
}
```

型充足アルゴリズムを拡張して、複数の入力を持つ関数を扱えるようにする。

#### 3b. Product型の導入

```dsl
type AllScopes = Scope1Emissions × Scope2Emissions × Scope3Emissions

fn aggregateAllScopes {
  sig: AllScopes -> TotalGHGEmissions
  impl: formula("total = scope1 + scope2 + scope3")
  ...
}
```

#### 3c. 依存型システム

値に依存する型を導入し、より精密な型検証を可能にする。

## 関連ドキュメント

- `doc/ghg_aggregate_analysis.md` - GHG集約関数の詳細分析
- `doc/theory/type_inhabitation.md` - 型充足問題の理論的背景

## 実行方法

### デモの実行

```bash
cd type_inhabitation_DSL
python3 demo_ghg_multipath.py
```

### 既存のテスト

```bash
# 問題が発生するテスト（Scope2だけが選ばれる）
python3 test_ghg_aggregate.py
```

## まとめ

**問題**: Facility → TotalGHGEmissions のパス探索で、Scope2だけの履歴しか残らない

**原因**:
- 型システムが単一入力関数しかサポートしていない
- 集約関数が実際には単一スコープの値をそのまま返している
- 探索アルゴリズムが最小コストのパス（Scope2経由）を選択

**現在の対応策**:
- 各スコープへのパスを個別に実行し、手動で合計する（`demo_ghg_multipath.py`）

**将来の拡張**:
- 多引数関数のサポート
- Product型の導入
- ワークフロー記述言語
- 依存型システム

この問題は、型理論ベースのオントロジー合成システムにおける**根本的な設計上の課題**であり、システムの進化において重要な研究テーマとなります。
