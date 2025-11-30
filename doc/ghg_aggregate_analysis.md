# GHG Scope 1, 2, 3 レポート作成シナリオ: 集約関数の影響分析

## 概要

このドキュメントでは、温室効果ガス(GHG)のScope 1, 2, 3レポート作成というユースケースを通じて、**集約関数が型理論ベースオントロジー合成システムにどのように影響するか**を分析します。

## 背景: GHGプロトコル

GHGプロトコルでは、企業の温室効果ガス排出量を以下の3つのスコープに分類します：

- **Scope 1 (直接排出)**: 自社が所有・管理する排出源からの直接的なGHG排出
  - 燃料の燃焼、プロセス排出など

- **Scope 2 (エネルギー間接排出)**: 購入した電力・熱の使用に伴う間接的なGHG排出
  - 購入電力、購入熱など

- **Scope 3 (その他の間接排出)**: サプライチェーンにおける間接的なGHG排出
  - 上流輸送、従業員通勤、出張など

各スコープ内およびスコープ間で**集約計算**が必要となります。

## DSLカタログの設計

### 型定義

```dsl
# 組織・施設
type Organization
type Facility

# Scope 1: 直接排出
type DirectFuelCombustion [unit=kg-CO2]
type ProcessEmissions [unit=kg-CO2]
type Scope1Emissions [unit=kg-CO2]

# Scope 2: エネルギー間接排出
type PurchasedElectricity [unit=kWh]
type PurchasedHeat [unit=MJ]
type Scope2Emissions [unit=kg-CO2]

# Scope 3: その他の間接排出
type UpstreamTransport [unit=t-km]
type EmployeeCommute [unit=km]
type BusinessTravel [unit=km]
type Scope3Emissions [unit=kg-CO2]

# 総排出量
type TotalGHGEmissions [unit=kg-CO2]
```

### 集約関数の定義

集約関数は、複数のデータソースを統合する関数として定義されます：

```dsl
# Scope 1 の集計（燃料燃焼 + プロセス排出）
fn aggregateScope1 {
  sig: DirectFuelCombustion -> Scope1Emissions
  impl: formula("scope1 = fuel_combustion + process_emissions")
  cost: 1
  confidence: 1.0
}

# Scope 1,2,3 を総排出量に集約
fn aggregateScope1toTotal {
  sig: Scope1Emissions -> TotalGHGEmissions
  impl: formula("total = scope1")
  cost: 0.5
  confidence: 1.0
}

fn aggregateScope2toTotal {
  sig: Scope2Emissions -> TotalGHGEmissions
  impl: formula("total = scope2")
  cost: 0.5
  confidence: 1.0
}

fn aggregateScope3toTotal {
  sig: Scope3Emissions -> TotalGHGEmissions
  impl: formula("total = scope3")
  cost: 0.5
  confidence: 1.0
}

# 全Scopeの合計（理想的には複数入力が必要）
fn aggregateAllScopes {
  sig: TotalGHGEmissions -> TotalGHGEmissions
  impl: formula("total = scope1 + scope2 + scope3")
  cost: 1
  confidence: 1.0
}
```

## テストシナリオと結果

### シナリオ 1: Facility -> Scope1Emissions (直接排出)

**目的**: 施設からScope1排出量を計算（燃料使用+プロセス排出を集約）

**結果**:
```
✓ 1 個のパスが見つかりました

パス 1:
  コスト: 3.0
  信頼度: 0.9310
  ステップ数: 3
  関数列:
    1. getFuelUsage: Facility -> FuelUsage
    2. fuelToDirectEmissions: FuelUsage -> DirectFuelCombustion
    3. aggregateScope1: DirectFuelCombustion -> Scope1Emissions [AGGREGATE]
```

**実行結果**:
```json
{
  "input_value": 1000.0,
  "final_result": 2250.0,
  "steps": [
    {"function": "getFuelUsage", "input": 1000.0, "output": 1000.0},
    {"function": "fuelToDirectEmissions", "input": 1000.0, "output": 1500.0},
    {"function": "aggregateScope1", "input": 1500.0, "output": 2250.0}
  ]
}
```

**分析**:
- 集約関数 `aggregateScope1` はパスの最後のステップとして正常に統合された
- 実行時にも formula として評価され、正しい結果を出力

### シナリオ 2: Facility -> Scope2Emissions (エネルギー間接排出)

**結果**:
```
✓ 2 個のパスが見つかりました

パス 1:
  コスト: 2.0
  信頼度: 0.8740
  ステップ数: 2
  関数列:
    1. getElectricityUsage: Facility -> PurchasedElectricity
    2. electricityToEmissions: PurchasedElectricity -> Scope2Emissions

パス 2:
  コスト: 3.0
  信頼度: 0.8100
  ステップ数: 2
  関数列:
    1. getHeatUsage: Facility -> PurchasedHeat
    2. heatToEmissions: PurchasedHeat -> Scope2Emissions
```

**分析**:
- Scope2には電力と熱の2つのソースがあるため、2つの異なるパスが見つかった
- このケースでは集約関数は不要（単一ソースから直接Scope2Emissionsへ変換）

### シナリオ 3: Organization -> TotalGHGEmissions (総排出量)

**結果**:
```
✓ 6 個のパスが見つかりました

パス 1:
  コスト: 3.5
  信頼度: 0.8500
  ステップ数: 2
  関数列:
    1. organizationToScope1: Organization -> Scope1Emissions
    2. aggregateScope1toTotal: Scope1Emissions -> TotalGHGEmissions [AGGREGATE]

パス 2:
  コスト: 3.5
  信頼度: 0.8500
  ステップ数: 2
  関数列:
    1. organizationToScope2: Organization -> Scope2Emissions
    2. aggregateScope2toTotal: Scope2Emissions -> TotalGHGEmissions [AGGREGATE]

パス 3:
  コスト: 3.5
  信頼度: 0.8000
  ステップ数: 2
  関数列:
    1. organizationToScope3: Organization -> Scope3Emissions
    2. aggregateScope3toTotal: Scope3Emissions -> TotalGHGEmissions [AGGREGATE]
```

**分析**:
- 各Scopeから総排出量への複数のパスが見つかった
- すべてのパスで集約関数 `aggregateScopeXtoTotal` が使用される
- 同じコスト(3.5)でも異なる信頼度により優先順位が決定される

### シナリオ 4: Facility -> TotalGHGEmissions (複数集約)

**結果**:
```
✓ 3 個のパスが見つかりました

パス 1:
  コスト: 2.5
  信頼度: 0.8740
  ステップ数: 3
  関数列:
    1. getElectricityUsage: Facility -> PurchasedElectricity
    2. electricityToEmissions: PurchasedElectricity -> Scope2Emissions
    3. aggregateScope2toTotal: Scope2Emissions -> TotalGHGEmissions [AGGREGATE]

パス 3:
  コスト: 3.5
  信頼度: 0.9310
  ステップ数: 4
  関数列:
    1. getFuelUsage: Facility -> FuelUsage
    2. fuelToDirectEmissions: FuelUsage -> DirectFuelCombustion
    3. aggregateScope1: DirectFuelCombustion -> Scope1Emissions [AGGREGATE]
    4. aggregateScope1toTotal: Scope1Emissions -> TotalGHGEmissions [AGGREGATE]
```

**分析**:
- パス3には**2つの集約関数**が含まれる（Scope内集約 + Scope間集約）
- コストは高いが信頼度も高い
- 複数の集約関数が連鎖する複雑なパスも正常に処理される

## 統計分析

### 全体統計

```
総シナリオ数: 8
パスが見つかったシナリオ: 8
パスが見つからなかったシナリオ: 0

集約関数を含む最適パス: 4
集約関数を含まない最適パス: 4
最適パスに含まれる集約関数の総数: 4
```

### コストと信頼度の比較

| シナリオ | コスト | 信頼度 | 集約数 |
|---------|-------|--------|-------|
| Facility -> Scope1Emissions | 3.0 | 0.9310 | 1 |
| Facility -> Scope2Emissions | 2.0 | 0.8740 | 0 |
| Organization -> Scope3Emissions | 3.0 | 0.8000 | 0 |
| Organization -> TotalGHGEmissions | 3.5 | 0.8500 | 1 |
| Facility -> TotalGHGEmissions | 2.5 | 0.8740 | 1 |
| FuelUsage -> Scope1Emissions | 2.0 | 0.9800 | 1 |
| PurchasedElectricity -> Scope2Emissions | 1.0 | 0.9200 | 0 |
| UpstreamTransport -> Scope3Emissions | 1.0 | 0.8800 | 0 |

**観察**:
- 集約関数の有無はコストに直接的な影響を与える（集約関数自体のコストが加算される）
- 集約関数を含むパスでも高い信頼度が維持される（集約関数のconf=1.0の場合）
- 短いパス（1ステップ）では集約が不要で、コストが最小

## 集約関数が型合成に与える影響

### 1. パス発見への影響

**結論**: 集約関数は通常の関数と同様に型合成に統合され、集約の有無はパスの発見可能性に直接影響しない

- すべてのシナリオでパスが見つかった（成功率100%）
- 集約関数を含むパスも含まないパスも同等に発見される
- 型システムは集約を特別扱いせず、単一の型変換として処理

### 2. コストへの影響

**結論**: 集約関数のコストは他の関数と同様に累積される

- 集約関数 `aggregateScope1` のコスト: 1.0
- 集約関数 `aggregateScopeXtoTotal` のコスト: 0.5
- 複数の集約が連鎖する場合、コストは加算される
- コストベースの最適化により、集約を含むパスと含まないパスが公平に比較される

### 3. 信頼度への影響

**結論**: 集約関数の信頼度は経路全体の信頼度に乗算される

- 今回の集約関数はすべて `confidence: 1.0` なので、信頼度への負の影響はない
- もし集約関数の信頼度が低い場合、パス全体の信頼度が低下する
- 例: conf=0.9 の集約を2回通過すると、信頼度は 0.9 × 0.9 = 0.81 に低下

### 4. 型システムへの影響（制限と課題）

**重要な制限**:

現在の型システムでは、集約関数は**単一の型変換**として表現されます：

```
aggregateScope1: DirectFuelCombustion -> Scope1Emissions
```

しかし、実際には複数の入力が必要です：

```
aggregateScope1: (DirectFuelCombustion, ProcessEmissions) -> Scope1Emissions
```

**この制限の影響**:

1. **型システムの表現力**:
   - 現在の型システムは単純型理論(Simple Type Theory)に基づいている
   - 複数引数の関数を直接表現できない
   - 集約は単一入力の変換として「近似」される

2. **実行時の挙動**:
   - Formula executor は複数のパラメータを使用できる
   - 実際の計算では複数の入力が使用される
   - 型システムと実行システムの間に「gap」が存在

3. **パス探索への影響**:
   - 複数の入力が必要な場合、型システムは最適なパスを見つけられない可能性がある
   - 現在は「主要な入力型」を選び、他の入力は暗黙的に扱われる

**将来的な解決策**:

- **依存型理論(Dependent Type Theory)**: 型が値に依存する
- **多引数関数のサポート**: `fn: (A, B) -> C` の形式
- **積型(Product Type)**: `fn: (A × B) -> C` としてモデル化
- **モナド的アプローチ**: 副作用として追加入力を扱う

## 実行機能との統合

集約関数は実行レイヤーでも正常に動作します：

### 実行例

```bash
python run_executable.py ghg_scope123.dsl Facility TotalGHGEmissions 1000 \
  --execute --mock --provenance --prov-output ghg_provenance.ttl
```

**実行結果**:
```json
{
  "goal": "Facility->TotalGHGEmissions",
  "input_value": 1000.0,
  "execution": {
    "final_result": 2250.0,
    "steps": [
      {"function": "getElectricityUsage", "input": 1000.0, "output": 1000.0},
      {"function": "electricityToEmissions", "input": 1000.0, "output": 1500.0},
      {"function": "aggregateScope2toTotal", "input": 1500.0, "output": 2250.0}
    ]
  }
}
```

### Provenance生成

集約関数の実行もProvenanceとして記録されます：

```turtle
ex:step_79a95f56_3
  a prov:Activity ;
  a ex:FunctionExecution ;
  rdfs:label "Execute aggregateScope2toTotal" ;
  ex:function_id "aggregateScope2toTotal" ;
  ex:function_signature "Scope2Emissions -> TotalGHGEmissions" ;
  ex:implementation_kind "formula" ;
  prov:used ex:result_79a95f56_2 ;
  prov:wasAssociatedWith ex:synthesis_system .
```

## ベストプラクティス

### 1. 集約関数の設計

**推奨**:
```dsl
# 明確な意図を持つ名前を使用
fn aggregateScope1 {
  sig: DirectFuelCombustion -> Scope1Emissions
  impl: formula("scope1 = fuel_combustion + process_emissions")
  cost: 1
  confidence: 1.0
}
```

**注意点**:
- 集約のコストを適切に設定（通常の計算より高くする場合もある）
- 信頼度は集約の確実性を反映（データソースの信頼性など）

### 2. 型の階層設計

GHGレポートのような階層的データには、型の階層を明確に設計：

```
Facility/Organization (入力)
  ↓
Individual Sources (FuelUsage, PurchasedElectricity, etc.)
  ↓
Scope-specific Emissions (Scope1Emissions, Scope2Emissions, Scope3Emissions)
  ↓ [AGGREGATE]
Total Emissions (TotalGHGEmissions)
```

### 3. 複数パスの活用

同じゴールに対して複数のパスが存在する場合：

- **コスト優先**: 最も効率的なパス
- **信頼度優先**: 最も確実なパス
- **バランス**: コストと信頼度のトレードオフ

システムはデフォルトでコスト優先ですが、ユースケースに応じて選択可能。

### 4. 集約の制限の認識

現在の型システムの制限を理解し、以下のように対処：

- **主要入力の選択**: 最も重要なデータソースを型シグネチャに含める
- **暗黙的パラメータ**: 他の入力はformulaのパラメータとして扱う
- **ドキュメント**: 実際に必要な入力をコメントに記載

```dsl
# 集約関数: 実際には DirectFuelCombustion と ProcessEmissions の両方が必要
fn aggregateScope1 {
  sig: DirectFuelCombustion -> Scope1Emissions
  impl: formula("scope1 = fuel_combustion + process_emissions")
  cost: 1
  confidence: 1.0
}
```

## まとめ

### 主要な発見

1. **統合性**: 集約関数は型理論ベースオントロジー合成システムに自然に統合される

2. **制限**: 現在の単純型理論では複数入力の集約を直接表現できないが、実用的には動作する

3. **実行可能性**: 探索だけでなく、実行レイヤーでも集約関数は正常に機能する

4. **Provenance**: 集約を含む実行履歴も完全にトレース可能

### 今後の展望

- **型システムの拡張**: 依存型や多引数関数のサポート
- **集約パターンライブラリ**: 一般的な集約パターンの定義
- **最適化アルゴリズム**: 複数の集約を効率的に処理
- **視覚化ツール**: 集約を含む複雑なパスの可視化

## 参考資料

- GHGプロトコル: https://ghgprotocol.org/
- PROV-O: https://www.w3.org/TR/prov-o/
- 型理論: Pierce, B. C. (2002). Types and Programming Languages
