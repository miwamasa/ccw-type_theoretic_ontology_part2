# 実行機能ガイド

## 概要

型理論ベースオントロジー合成システムに、以下の3つの実行機能が追加されました：

1. **実行レイヤー**: SPARQL/REST/Formula の実際の実行
2. **単位変換**: 自動的な単位変換関数の挿入
3. **Provenance**: PROV-O形式での来歴記録

これらの機能により、パス探索だけでなく、実際の値の計算と結果の記録が可能になりました。

## 新しいモジュール

### 1. executor.py - 実行レイヤー

関数の実装を実際に実行するエンジン。

**主要クラス:**
- `FormulaExecutor`: 数式を評価
- `SPARQLExecutor`: SPARQLクエリを実行
- `RESTExecutor`: REST APIを呼び出し
- `PathExecutor`: 型合成パス全体を実行

**実行コンテキスト:**
```python
from executor import ExecutionContext

context = ExecutionContext(
    parameters={
        'emission_factor': 2.7,  # kg-CO2/kg-fuel
        'energy_density': 42e6,  # J/kg
        'efficiency': 0.35
    },
    sparql_endpoint='http://localhost:7200/repositories/myrepo',
    mock_mode=False,  # 実際に実行
    record_provenance=True
)
```

**実行例:**
```python
from synth_lib import Catalog, synthesize_backward
from executor import PathExecutor, create_mock_context

# パスを探索
cat = Catalog.from_dsl('catalog.dsl')
results = synthesize_backward(cat, src_type='Product', goal_type='CO2')
cost, path = results[0]

# パスを実行
context = create_mock_context()
executor = PathExecutor()
final_result, steps = executor.execute_path(path, input_value=360000, context=context)

print(f"結果: {final_result} kg-CO2")
```

### 2. unit_converter.py - 単位変換

型の単位情報を解析し、必要に応じて単位変換を自動挿入。

**サポートされる単位:**
- エネルギー: J, kJ, MJ, GJ, Wh, kWh, MWh, cal, kcal
- 質量: g, kg, t, lb, oz
- 長さ: m, km, cm, mm, ft, in
- 体積: L, mL, m3, gal
- 時間: s, min, h, day
- 温度: K, C, F

**使用例:**
```python
from unit_converter import UnitConverter

converter = UnitConverter()

# エネルギー変換
j = converter.convert(100, 'kWh', 'J')  # 360,000,000 J

# 質量変換
kg = converter.convert(1, 'lb', 'kg')  # 0.453592 kg

# 温度変換
k = converter.convert(25, 'C', 'K')  # 298.15 K
```

**自動挿入:**
```python
from unit_converter import UnitAwareCatalog

unit_catalog = UnitAwareCatalog(catalog)

# パスに単位変換を自動挿入
augmented_path = unit_catalog.augment_path_with_conversions(
    path, src_type='Product', goal_type='CO2'
)
```

### 3. provenance.py - Provenance生成

PROV-O（W3C Provenance Ontology）形式で実行の来歴を記録。

**Provenance要素:**
- **Entity**: データ（入力、中間結果、最終結果）
- **Activity**: 実行アクティビティ（関数呼び出し）
- **Agent**: システム（合成エンジン）

**使用例:**
```python
from provenance import ProvenanceGenerator

generator = ProvenanceGenerator()
prov = generator.generate_synthesis_provenance(
    synthesis_id='run_001',
    goal='Product->CO2',
    path=path,
    input_value=360000,
    output_value=final_result,
    execution_steps=steps,
    context=context
)

# Turtle形式で出力
with open('provenance.ttl', 'w') as f:
    f.write(prov.to_turtle())

# JSON形式で出力
with open('provenance.json', 'w') as f:
    f.write(prov.to_json())
```

## 統合スクリプト: run_executable.py

すべての機能を統合したコマンドラインツール。

### 基本的な使い方

```bash
# 探索のみ（既存機能）
python run_executable.py catalog.dsl Product CO2 360000

# 実行モード
python run_executable.py catalog.dsl Product CO2 360000 --execute --mock

# Provenance生成
python run_executable.py catalog.dsl Product CO2 360000 \
  --execute --mock --provenance --prov-output result.ttl

# 単位変換を有効化
python run_executable.py catalog.dsl Product Energy 100 \
  --execute --mock --unit-conversion
```

### コマンドラインオプション

| オプション | 説明 |
|----------|------|
| `--execute` | パスを実際に実行 |
| `--mock` | モック実行モード（外部依存なし） |
| `--sparql-endpoint URL` | SPARQLエンドポイントのURL |
| `--param KEY=VALUE` | 実行パラメータ（複数指定可） |
| `--provenance` | Provenance生成を有効化 |
| `--prov-format {turtle,json}` | Provenance出力形式 |
| `--prov-output FILE` | Provenance出力ファイル |
| `--unit-conversion` | 自動単位変換を有効化 |
| `--max-cost N` | 最大コスト制限 |
| `--verbose` | 詳細出力 |

### パラメータの指定

実行時に必要なパラメータを指定：

```bash
python run_executable.py catalog.dsl Product CO2 360000 \
  --execute --mock \
  --param emission_factor=2.7 \
  --param energy_density=42000000 \
  --param efficiency=0.35
```

デフォルト値：
- `emission_factor`: 2.7 (kg-CO2/kg-fuel)
- `energy_density`: 42,000,000 (J/kg, gasoline)
- `efficiency`: 0.35

## 実行例

### 例1: CFP計算（モックモード）

```bash
python run_executable.py catalog.dsl Product CO2 360000 \
  --execute --mock --verbose
```

**出力:**
```json
{
  "goal": "Product->CO2",
  "input_value": 360000.0,
  "path": {
    "cost": 5.0,
    "confidence": 0.7056,
    "steps": [
      {"id": "usesEnergy", "sig": "Product -> Energy", ...},
      {"id": "energyToFuelEstimate", "sig": "Energy -> Fuel", ...},
      {"id": "fuelToCO2", "sig": "Fuel -> CO2", ...}
    ],
    "proof": "usesEnergy ∘ energyToFuelEstimate ∘ fuelToCO2"
  },
  "execution": {
    "final_result": 23.14,
    "steps": [
      {"step": 1, "function": "usesEnergy", "input": 360000, "output": 360000},
      {"step": 2, "function": "energyToFuelEstimate", "input": 360000, "output": 8.57},
      {"step": 3, "function": "fuelToCO2", "input": 8.57, "output": 23.14}
    ],
    "parameters_used": {...},
    "mock_mode": true
  }
}
```

### 例2: Provenanceを含む完全な実行

```bash
python run_executable.py catalog.dsl Product CO2 360000 \
  --execute --mock \
  --provenance --prov-output result.ttl \
  --verbose
```

**生成されるProvenance（result.ttl）:**
```turtle
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix ex: <http://example.org/> .

ex:input_12345
  a prov:Entity ;
  a ex:InputData ;
  prov:value "360000.0"^^xsd:double .

ex:step_12345_1
  a prov:Activity ;
  a ex:FunctionExecution ;
  rdfs:label "Execute usesEnergy" ;
  prov:used ex:input_12345 ;
  ex:function_id "usesEnergy" ;
  ex:function_signature "Product -> Energy" .

ex:result_12345_1
  a prov:Entity ;
  a ex:IntermediateResult ;
  prov:value "360000.0"^^xsd:double ;
  prov:wasGeneratedBy ex:step_12345_1 ;
  prov:wasDerivedFrom ex:input_12345 .

# ... 以下続く
```

### 例3: SPARQL実行（実際のエンドポイント使用）

```bash
python run_executable.py catalog.dsl Product CO2 360000 \
  --execute \
  --sparql-endpoint http://localhost:7200/repositories/myrepo \
  --param emission_factor=2.7
```

**注意**: SPARQLエンドポイントを使用する場合、`SPARQLWrapper`ライブラリが必要：
```bash
pip install sparqlwrapper
```

## モックモード vs 実行モード

### モックモード（`--mock`）

- 外部依存なしで動作
- SPARQLやRESTは実際には呼び出されない
- テストや開発に適している
- パラメータに基づいて計算は行われる

### 実行モード（`--execute`のみ）

- 実際にSPARQLエンドポイントやREST APIを呼び出す
- 実データを使用
- 本番環境での使用を想定
- 外部サービスへのアクセスが必要

## Provenanceの活用

生成されたProvenanceは以下の用途に使用できます：

### 1. 監査証跡

実行の完全な記録として、監査やコンプライアンスに使用。

### 2. 再現性

同じ入力とパラメータで結果を再現可能。

### 3. データ系譜

データがどの関数を通ってどのように変換されたかを追跡。

### 4. 信頼性評価

各ステップの信頼度を記録し、結果の信頼性を評価。

### 5. RDFグラフとしての統合

他のRDFデータと統合し、SPARQL で問い合わせ可能：

```sparql
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX ex: <http://example.org/>

SELECT ?activity ?function ?input ?output
WHERE {
  ?activity a prov:Activity ;
           ex:function_id ?function ;
           prov:used ?input_entity ;
           prov:generated ?output_entity .
  ?input_entity prov:value ?input .
  ?output_entity prov:value ?output .
}
```

## 既存機能との互換性

### 探索のみの実行（既存機能）

既存のスクリプトはそのまま動作：

```bash
# run_dsl.py（探索のみ）
python run_dsl.py catalog.dsl Product CO2

# run_executable.py（探索のみ、--executeなし）
python run_executable.py catalog.dsl Product CO2 360000
```

### 段階的な移行

1. **段階1**: 探索のみ使用（既存）
2. **段階2**: モック実行でテスト（`--execute --mock`）
3. **段階3**: 実際の実行（`--execute`）
4. **段階4**: Provenance生成（`--provenance`）

## トラブルシューティング

### SPARQLWrapperがない

```
Warning: SPARQLWrapper not found. SPARQL execution will not work.
```

**解決策:**
```bash
pip install sparqlwrapper
```

または、モックモードを使用：
```bash
python run_executable.py ... --mock
```

### Requestsがない

```
Warning: requests library not found. REST API execution will not work.
```

**解決策:**
```bash
pip install requests
```

### パラメータが不足

Formulaの実行時にパラメータが不足している場合、エラーまたはデフォルト値が使用されます。

**解決策:**
```bash
python run_executable.py ... \
  --param efficiency=0.35 \
  --param emission_factor=2.7
```

## まとめ

実行機能の追加により、型理論ベースオントロジー合成システムは：

- ✅ パス探索（既存）
- ✅ 実際の値の計算（新）
- ✅ 単位変換の自動化（新）
- ✅ 実行記録のProvenance生成（新）

を統合的にサポートするフルスタックシステムになりました。

探索モードと実行モードを選択でき、既存のコードとの互換性も維持されています。
