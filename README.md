# 型理論ベース オントロジー探索・合成システム

Type-Theoretic Ontology Synthesis System

## 概要

本プロジェクトは、**型理論**と**圏論**に基づくオントロジー探索・合成システムです。CFP（Carbon Footprint）計算などの複雑なオントロジー間変換を、**type inhabitation（型充足）問題**として定式化し、自動的に変換パスを探索・合成します。

### 主な特徴

- 🔍 **自動パス探索**: 目的型を指定するだけで、最適な変換パスを自動発見
- 📊 **コスト・信頼度の最適化**: コスト最小、信頼度を考慮したパス選択
- 🎯 **型理論的健全性**: 型導出に基づく厳密な変換合成
- 🔄 **Span/Cospan理論**: 圏論的なオントロジーアライメント
- 📝 **専用DSL**: 読みやすく、拡張可能な型・関数定義言語
- ⚡ **実行レイヤー**: SPARQL/REST/Formula の実際の実行（新機能）
- 🔧 **単位変換**: 自動的な単位変換関数の挿入（新機能）
- 📋 **Provenance**: PROV-O形式での来歴記録（新機能）
- ✅ **検証済み**: すべてのテストが成功

## プロジェクト構成

```
.
├── theory/                      # 理論的基礎
│   ├── span_cospan.md          # Span/Cospan によるオントロジー理論
│   ├── dsl_design.md           # DSL設計書
│   └── cfp_example.md          # CFP例題の理論解説
│
├── type_inhabitation_DSL/      # DSLと実装
│   ├── catalog.dsl             # DSL形式のカタログ（推奨）
│   ├── catalog.yaml            # YAML形式のカタログ（互換性用）
│   ├── dsl_parser.py           # DSLパーサー
│   ├── synth_lib.py            # 型合成ライブラリ
│   ├── executor.py             # 実行レイヤー（新）
│   ├── unit_converter.py       # 単位変換システム（新）
│   ├── provenance.py           # Provenance生成（新）
│   ├── run_dsl.py              # DSL実行スクリプト
│   ├── run_executable.py       # 実行可能スクリプト（新）
│   ├── run_prototype.py        # YAML実行スクリプト
│   ├── test_dsl.py             # DSL統合テスト
│   ├── test_execution.py       # 実行機能テスト（新）
│   └── test_synthesis.py       # 型合成テスト
│
├── doc/                        # ドキュメント
│   ├── implementation.md       # 実装の詳細説明
│   ├── verification_results.md # 動作確認結果
│   ├── cfp_solution.md         # CFP例題の解題
│   ├── dsl_guide.md            # DSLガイド
│   └── execution_guide.md      # 実行機能ガイド（新）
│
└── README.md                   # このファイル
```

## クイックスタート

### 必要環境

- Python 3.9+
- PyYAML

### インストール

**基本機能（探索のみ）:**
```bash
pip install pyyaml
```

**実行機能も使用する場合（オプション）:**
```bash
pip install pyyaml requests sparqlwrapper
```

### 基本的な使い方

#### 1. DSLファイルを使った実行（推奨）

```bash
cd type_inhabitation_DSL

# Product から CO2 への変換パスを探索
python run_dsl.py catalog.dsl Product CO2
```

**出力例:**
```json
{
  "goal": "Product->CO2",
  "plans": [
    {
      "cost": 5.0,
      "confidence_est": 0.7056,
      "steps": [
        {"id": "usesEnergy", "sig": "Product -> Energy", ...},
        {"id": "energyToFuelEstimate", "sig": "Energy -> Fuel", ...},
        {"id": "fuelToCO2", "sig": "Fuel -> CO2", ...}
      ],
      "proof": "usesEnergy ∘ energyToFuelEstimate ∘ fuelToCO2"
    }
  ]
}
```

#### 2. プログラムから使用

```python
from synth_lib import Catalog, synthesize_backward

# DSLファイルからカタログを読み込み
cat = Catalog.from_dsl('catalog.dsl')

# 型合成を実行
results = synthesize_backward(cat, src_type='Product', goal_type='CO2')

for cost, path in results:
    print(f"Cost: {cost}")
    funcs = ' ∘ '.join([p.id for p in path])
    print(f"Functions: {funcs}")
```

#### 3. 実行機能の使用（新機能）

**パスの実際の実行:**
```bash
# モック実行（外部依存なし）
python run_executable.py catalog.dsl Product CO2 360000 --execute --mock

# Provenance生成を含む完全な実行
python run_executable.py catalog.dsl Product CO2 360000 \
  --execute --mock \
  --provenance --prov-output result.ttl \
  --verbose
```

詳細は [`doc/execution_guide.md`](doc/execution_guide.md) を参照。

#### 4. テストの実行

```bash
# DSL統合テスト
python test_dsl.py

# 型合成テスト
python test_synthesis.py

# 実行機能テスト（新）
python test_execution.py
```

## DSL構文

### 型定義

```
type Product
type Energy [unit=J, range=>=0]
type Fuel [unit=kg]
type CO2 [unit=kg]
```

### 関数定義

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

詳細は [`doc/dsl_guide.md`](doc/dsl_guide.md) を参照。

## 理論的背景

### Type Inhabitation（型充足）

目的型 `Product -> CO2` を満たす証明項（関数合成）を探索する問題として定式化：

```
Γ ⊢ usesEnergy : Product → Energy
Γ ⊢ energyToFuelEstimate : Energy → Fuel
Γ ⊢ fuelToCO2 : Fuel → CO2
───────────────────────────────────────────────────────
Γ ⊢ (fuelToCO2 ∘ energyToFuelEstimate ∘ usesEnergy) : Product → CO2
```

### Span/Cospan合成

各関数を圏の射として、スパンの合成により変換パスを構築：

```
Product --usesEnergy--> Energy --energyToFuelEstimate--> Fuel --fuelToCO2--> CO2
```

Pullback により、型が一致する場合のみ合成可能。

### 中間型の自動発見

探索の過程で、`Energy` と `Fuel` という**隠れたブリッジ概念**が自動的に発見される現象を実証。

詳細は以下を参照：
- [`theory/span_cospan.md`](theory/span_cospan.md)
- [`theory/dsl_design.md`](theory/dsl_design.md)
- [`theory/cfp_example.md`](theory/cfp_example.md)

## 実装の詳細

### 探索アルゴリズム

**逆方向探索（Backward Search）** を使用：

1. ゴール型から開始
2. ゴール型を返す関数を探索
3. 各関数のドメインを新しいサブゴールとする
4. ソース型に到達するまで繰り返す
5. コスト最小のパスを返す

**特徴:**
- Dijkstra的な最短経路探索
- コスト制限による枝刈り
- 訪問済みノードの重複除去

詳細は [`doc/implementation.md`](doc/implementation.md) を参照。

## 動作確認結果

すべてのテストが成功：

- ✅ 基本動作: Product → CO2 のパス探索成功
- ✅ 包括的テスト: 6つのテストケースすべて成功
- ✅ DSL統合テスト: 5つのテストケースすべて成功
- ✅ 型理論・圏論との整合性確認

詳細は [`doc/verification_results.md`](doc/verification_results.md) を参照。

## CFP計算の例

**問題**: 製品（Product）のカーボンフットプリント（CO2排出量）を計算

**発見されたパス**:
```
Product → Energy → Fuel → CO2
```

**使用された関数**:
1. `usesEnergy`: Product → Energy (cost=1, conf=0.9)
2. `energyToFuelEstimate`: Energy → Fuel (cost=3, conf=0.8, inverse)
3. `fuelToCO2`: Fuel → CO2 (cost=1, conf=0.98)

**メトリクス**:
- 総コスト: 5.0
- 総信頼度: 0.7056 (= 0.9 × 0.8 × 0.98)

詳細な解題は [`doc/cfp_solution.md`](doc/cfp_solution.md) を参照。

## ドキュメント

### 理論
- [`theory/span_cospan.md`](theory/span_cospan.md) - Span/Cospan によるオントロジー理論
- [`theory/dsl_design.md`](theory/dsl_design.md) - DSL設計の理論的背景
- [`theory/cfp_example.md`](theory/cfp_example.md) - 中間型の出現メカニズム

### 実装・使い方
- [`doc/dsl_guide.md`](doc/dsl_guide.md) - DSL完全ガイド（推奨）
- [`doc/execution_guide.md`](doc/execution_guide.md) - 実行機能ガイド（新）
- [`doc/implementation.md`](doc/implementation.md) - 実装の詳細
- [`doc/cfp_solution.md`](doc/cfp_solution.md) - CFP例題の詳細解題
- [`doc/verification_results.md`](doc/verification_results.md) - 動作確認結果

## 実装済み機能と今後の拡張

### 実装済み ✅
- [x] **実行レイヤー**: SPARQL/REST/Formula の実際の実行
- [x] **単位変換**: 自動的な単位変換関数の挿入
- [x] **Provenance**: PROV-O形式での来歴記録
- [x] **DSL**: 専用の型・関数定義言語
- [x] **型合成**: 逆方向探索による最適パス発見
- [x] **コスト・信頼度**: メトリクスに基づく最適化

### 今後の拡張

### 中期（アルゴリズム改善）
- [ ] A*探索: ヒューリスティクス関数の導入
- [ ] 双方向探索: 起点と終点からの同時探索
- [ ] キャッシング: 型到達可能性のキャッシュ

### 長期（理論的拡張）
- [ ] 依存型: 値に依存する型の導入
- [ ] 証明項の検証: Lean4等での形式検証
- [ ] 多引数関数: カリー化を超えた多引数サポート
- [ ] Cospan/Colimit: オントロジー統合機能

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## ライセンス

[MIT License](LICENSE)

## 引用

本プロジェクトを研究で使用する場合、以下の形式で引用してください：

```
Type-Theoretic Ontology Synthesis System
https://github.com/miwamasa/ccw-type_theoretic_ontology_part2
```

## 関連プロジェクト

- [NGSI-LD](https://www.etsi.org/deliver/etsi_gs/CIM/001_099/009/01.08.01_60/gs_CIM009v010801p.pdf) - Context Information Management
- [RDF](https://www.w3.org/RDF/) - Resource Description Framework
- [PROV-O](https://www.w3.org/TR/prov-o/) - Provenance Ontology

## 謝辞

本プロジェクトは、型理論、圏論、オントロジー工学の研究成果に基づいています。
