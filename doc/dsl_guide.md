# 型理論ベースオントロジー合成システム - DSLガイド

## 概要

本DSL（Domain-Specific Language）は、型理論と圏論に基づくオントロジー合成システムのための専用言語です。型と関数を宣言的に定義し、自動的に型充足問題を解いて変換パスを探索します。

## DSLの目的

- **宣言的な記述**: 型と関数を簡潔に記述
- **可読性**: YAML よりも読みやすく、自然な構文
- **型安全性**: 型シグネチャの明示
- **メタデータ**: コスト、信頼度、逆関数などを記述

## 基本構文

### 型宣言

```
type <型名> [<属性リスト>]
```

**例:**

```
type Product
type Energy [unit=J, range=>=0]
type Fuel [unit=kg]
type CO2 [unit=kg]
```

**属性:**
- `unit`: 単位（例: `J`, `kg`, `m`）
- `range`: 値の範囲（例: `>=0`, `>0`, `0..100`）
- その他カスタム属性も可能

### 関数宣言

```
fn <関数名> {
  sig: <ドメイン型> -> <コドメイン型>
  impl: <実装仕様>
  cost: <コスト（数値）>
  confidence: <信頼度（0.0〜1.0）>
  inverse_of: <逆関数名>（オプション）
}
```

**例:**

```
fn usesEnergy {
  sig: Product -> Energy
  impl: sparql("SELECT ?p ?e WHERE { ?p :usesEnergy ?e }")
  cost: 1
  confidence: 0.9
}

fn fuelToCO2 {
  sig: Fuel -> CO2
  impl: formula("co2 = fuel_amount * emission_factor")
  cost: 1
  confidence: 0.98
}

fn energyToFuelEstimate {
  sig: Energy -> Fuel
  impl: formula("fuel = energy / efficiency")
  cost: 3
  confidence: 0.8
  inverse_of: fuelToEnergy
}
```

## 実装仕様（impl）

関数の実装方法を指定します。

### 1. SPARQL

RDFトリプルストアへのクエリ：

```
impl: sparql("<SPARQL クエリ>")
```

**例:**
```
impl: sparql("SELECT ?p ?e WHERE { ?p :usesEnergy ?e }")
```

ネストした括弧も使用可能：
```
impl: sparql("SELECT ?p ?e WHERE { ?p :hasEnergy ?e . FILTER(?e > 0) }")
```

### 2. Formula

数式による計算：

```
impl: formula("<数式>")
```

**例:**
```
impl: formula("co2 = fuel_amount * emission_factor")
impl: formula("energy = fuel * energy_density")
```

### 3. REST

REST API呼び出し：

```
impl: rest("<メソッド>, <URL>")
```

**例:**
```
impl: rest("POST, https://api.example.com/convert")
impl: rest("GET, https://api.example.com/data/{id}")
```

### 4. カスタム実装

独自の実装タイプも定義可能：

```
impl: python_script("path/to/script.py")
impl: ml_model("model_name")
```

## コストと信頼度

### コスト（cost）

関数の実行コストを表す数値。探索時に最小コストのパスが優先されます。

**ガイドライン:**
- SPARQL クエリ: 1〜2
- 簡単な数式: 1
- REST API 呼び出し: 2〜5
- 逆算・推定: 3〜5（不確実性が高いためコスト増）
- ML モデル: 5〜10

### 信頼度（confidence）

結果の信頼度を 0.0〜1.0 で表します。複数の関数を合成する際、信頼度は積で計算されます。

**ガイドライン:**
- 確定的な変換: 0.95〜1.0
- データベースからの取得: 0.85〜0.95（データ品質に依存）
- 逆算・推定: 0.7〜0.85
- ML 推定: 0.5〜0.8

**例:**
```
パス: usesEnergy (0.9) ∘ energyToFuelEstimate (0.8) ∘ fuelToCO2 (0.98)
信頼度: 0.9 × 0.8 × 0.98 = 0.7056
```

## 逆関数（inverse_of）

ある関数の逆関数を定義する場合、`inverse_of` 属性を使用します。

**例:**

```
fn fuelToEnergy {
  sig: Fuel -> Energy
  impl: formula("energy = fuel_amount * energy_density")
  cost: 2
  confidence: 0.95
}

fn energyToFuelEstimate {
  sig: Energy -> Fuel
  impl: formula("fuel = energy / efficiency")
  cost: 3
  confidence: 0.8
  inverse_of: fuelToEnergy
}
```

**逆関数の特徴:**
- 通常、コストが高い（不確実性による）
- 信頼度が低い（推定を伴うため）
- 探索で自動的に考慮される

## コメント

`#` 以降はコメントとして扱われます。

```
# これはコメントです
type Product  # 製品型

# CFP計算用の関数
fn usesEnergy {
  sig: Product -> Energy
  # ...
}
```

## 完全な例: CFP計算

```
# CFP (Carbon Footprint) 計算用カタログ
# 型理論ベースオントロジー合成システム DSL

# 型定義
type Product

type Energy [unit=J, range=>=0]

type Fuel [unit=kg]

type CO2 [unit=kg]

# 関数定義

# 製品のエネルギー使用量を取得
fn usesEnergy {
  sig: Product -> Energy
  impl: sparql("SELECT ?p ?e WHERE { ?p :usesEnergy ?e }")
  cost: 1
  confidence: 0.9
}

# 燃料からエネルギーへの変換
fn fuelToEnergy {
  sig: Fuel -> Energy
  impl: formula("energy = fuel_amount * energy_density")
  cost: 2
  confidence: 0.95
}

# 燃料からCO2への変換
fn fuelToCO2 {
  sig: Fuel -> CO2
  impl: formula("co2 = fuel_amount * emission_factor")
  cost: 1
  confidence: 0.98
}

# エネルギーから燃料への逆推定
fn energyToFuelEstimate {
  sig: Energy -> Fuel
  impl: formula("fuel = energy / efficiency")
  cost: 3
  confidence: 0.8
  inverse_of: fuelToEnergy
}
```

## 使用方法

### 1. DSLファイルの作成

カタログを `.dsl` 拡張子のファイルで作成します。

```bash
# catalog.dsl を作成
vim catalog.dsl
```

### 2. DSLからYAMLへの変換（オプション）

```bash
python dsl_parser.py catalog.dsl catalog.yaml
```

これにより、既存のYAMLベースのツールとも互換性が保たれます。

### 3. DSLファイルを直接使用

```bash
python run_dsl.py catalog.dsl Product CO2
```

**出力:**
```json
{
  "goal": "Product->CO2",
  "plans": [
    {
      "cost": 5.0,
      "confidence_est": 0.7056,
      "steps": [...],
      "proof": "usesEnergy ∘ energyToFuelEstimate ∘ fuelToCO2"
    }
  ]
}
```

### 4. プログラムから使用

```python
from synth_lib import Catalog, synthesize_backward

# DSLファイルからカタログを読み込み
cat = Catalog.from_dsl('catalog.dsl')

# 型合成を実行
results = synthesize_backward(cat, src_type='Product', goal_type='CO2')

for cost, path in results:
    print(f"Cost: {cost}")
    print(f"Path: {' -> '.join([p.dom for p in path] + [path[-1].cod])}")
```

## DSLの利点

### 1. 可読性

**YAML:**
```yaml
functions:
  - id: usesEnergy
    sig: "Product -> Energy"
    impl:
      kind: sparql
      query: "SELECT ?p ?e WHERE { ?p :usesEnergy ?e }"
    cost: 1
    confidence: 0.9
```

**DSL:**
```
fn usesEnergy {
  sig: Product -> Energy
  impl: sparql("SELECT ?p ?e WHERE { ?p :usesEnergy ?e }")
  cost: 1
  confidence: 0.9
}
```

DSLの方が関数定義として自然で読みやすい。

### 2. 型シグネチャの明示

`sig: Product -> Energy` という形式で、型理論的な記法を直接使用。

### 3. 拡張性

新しい属性や実装タイプを簡単に追加可能。

### 4. ツールサポート

- パーサーが明確なエラーメッセージを提供
- シンタックスハイライトが可能
- IDE補完のサポートが容易

## 型理論的解釈

DSLで定義された関数は、型理論における**公理（axioms）**に対応します。

```
fn f {
  sig: A -> B
  ...
}
```

これは以下の型付けルールに対応：

```
Γ ⊢ f : A → B
```

複数の関数を組み合わせることで、**型導出（type derivation）**が行われます：

```
Γ ⊢ f : A → B    Γ ⊢ g : B → C
─────────────────────────────── [composition]
Γ ⊢ g ∘ f : A → C
```

DSLシステムは、目的型 `A -> C` を満たす証明項（関数合成）を自動的に探索します。

## 圏論的解釈

各関数は圏における**射（morphism）**に対応：

```
f: A → B
g: B → C
```

これらの射の**合成（composition）**：

```
g ∘ f: A → C
```

が自動的に計算されます。

`inverse_of` で指定された逆関数は、スパン（span）の逆方向の射として扱われます。

## エラー処理

### 構文エラー

**誤:**
```
fn badFunc {
  sig Product -> Energy  # ":" が抜けている
}
```

**正:**
```
fn badFunc {
  sig: Product -> Energy
}
```

### 型シグネチャのエラー

**誤:**
```
fn badSig {
  sig: ProductEnergy  # "->" が抜けている
}
```

**正:**
```
fn badSig {
  sig: Product -> Energy
}
```

### ネストした括弧

DSLパーサーは文字列リテラル内の括弧を正しく処理します：

**正常に処理:**
```
fn complexQuery {
  sig: A -> B
  impl: sparql("SELECT ?a ?b WHERE { ?a :prop ?b . FILTER(?b > 0) }")
}
```

## ベストプラクティス

### 1. 型の整理

関連する型をグループ化：

```
# エネルギー関連の型
type Energy [unit=J]
type Power [unit=W]
type Fuel [unit=kg]

# 環境影響の型
type CO2 [unit=kg]
type WaterFootprint [unit=L]
```

### 2. 関数の命名

- 明確で説明的な名前を使用
- 動詞形を推奨（`convertFuelToEnergy`, `calculateCO2`）
- 逆関数には `Estimate` や `Inverse` を付ける

### 3. コストと信頼度の設定

- 実測に基づいて設定
- 不確実性が高い場合はコストを上げ、信頼度を下げる
- 一貫性を保つ（同じ種類の操作には同じコスト範囲）

### 4. コメントの活用

```
# このセクションは製品のライフサイクル分析に関する関数群です
# 参照: LCA標準 ISO 14040:2006

fn productionEnergy {
  sig: Product -> Energy
  # 製造段階のエネルギー消費量を計算
  impl: sparql("SELECT ?p ?e WHERE { ?p :productionEnergy ?e }")
  cost: 1
  confidence: 0.85  # データの完全性に依存
}
```

### 5. モジュール化

大規模なカタログは複数のファイルに分割することを検討：

```
catalog/
  ├── types.dsl          # 型定義のみ
  ├── energy.dsl         # エネルギー関連の関数
  ├── emissions.dsl      # 排出量計算の関数
  └── conversions.dsl    # 単位変換の関数
```

## トラブルシューティング

### パスが見つからない

**症状:** `No path found from A to B`

**原因:**
- 型グラフが連結していない
- コスト制限が厳しすぎる

**解決策:**
```bash
# コスト制限を上げる
python run_dsl.py catalog.dsl A B 100
```

### 信頼度が低すぎる

**症状:** 見つかったパスの信頼度が実用に耐えない

**解決策:**
- より直接的な関数を追加
- 逆算ステップを減らす
- データの品質を向上

### パーサーエラー

**症状:** DSLファイルのパースに失敗

**解決策:**
- 構文をチェック（特に括弧の対応）
- 文字列リテラルを引用符で囲む
- コメントアウトで問題箇所を特定

## 今後の拡張

### 計画中の機能

1. **多引数関数**: `sig: (A, B) -> C`
2. **依存型**: `sig: (x: Energy) -> Fuel { f | f * density = x }`
3. **型制約**: `where Energy > 0`
4. **マクロ**: 頻出パターンの抽象化
5. **インポート**: `import energy.dsl`

### コミュニティへの貢献

- カタログの共有（GitHub等）
- ベストプラクティスの文書化
- DSL拡張の提案

## 参考資料

- `theory/dsl_design.md`: DSL設計の理論的背景
- `theory/span_cospan.md`: 圏論的基礎
- `doc/implementation.md`: 実装の詳細
- `doc/cfp_solution.md`: CFP計算の実例

## まとめ

型理論ベースオントロジー合成システムのDSLは、以下を実現します：

- ✓ 宣言的で読みやすい型・関数定義
- ✓ 型理論・圏論の概念の直接的な表現
- ✓ 自動的な型充足問題の解決
- ✓ コスト・信頼度を考慮した最適パス探索
- ✓ YAML等の既存形式との互換性

本DSLを使用することで、複雑なオントロジー間の変換を簡潔に記述し、自動的に実行可能なワークフローを生成できます。
