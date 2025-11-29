# 型理論ベース オントロジー合成システム - 実装説明

## 概要

本システムは、型理論と圏論に基づくオントロジー探索・合成システムである。CFP（Carbon Footprint）計算などの複雑な変換を、**type inhabitation（型充足）問題**として定式化し、自動的に変換パスを探索・合成する。

## 理論的基礎

本実装は以下の理論に基づいている：

1. **Span/Cospan理論**（`theory/span_cospan.md`参照）
   - オントロジー間のアライメントをスパンとして表現
   - スパンの合成によるマッピングの連鎖
   - Pullbackによる意味的な接続の保証

2. **型理論による型充足**（`theory/dsl_design.md`参照）
   - 型 = オントロジーのクラス
   - 関数 = 型間の変換
   - 目的型を満たす関数列の探索

3. **中間型の自動導出**（`theory/cfp_example.md`参照）
   - 探索による隠れたブリッジ概念の発見
   - 型制約充足による中間型推論

## アーキテクチャ

### 主要コンポーネント

```
type_inhabitation_DSL/
├── catalog.yaml         # 型と関数のカタログ（DSL）
├── synth_lib.py        # 型合成ライブラリ
├── run_prototype.py    # 実行スクリプト
└── test_synthesis.py   # テストスイート
```

### 1. カタログ定義（catalog.yaml）

型と関数を宣言的に定義するDSL。

**型定義:**
```yaml
types:
  - name: Product
  - name: Energy
    unit: J
    range: ">=0"
  - name: Fuel
    unit: kg
  - name: CO2
    unit: kg
```

**関数定義:**
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

各関数は以下の属性を持つ：
- `id`: 関数識別子
- `sig`: 型シグネチャ（`Domain -> Codomain`）
- `impl`: 実装情報（SPARQL、REST、formula等）
- `cost`: 実行コスト
- `confidence`: 信頼度（0.0〜1.0）
- `inverse_of`: 逆関数の指定（オプション）

### 2. 型合成ライブラリ（synth_lib.py）

#### データ構造

**Func クラス:**
```python
@dataclass
class Func:
    id: str           # 関数ID
    dom: str          # Domain型
    cod: str          # Codomain型
    cost: float       # コスト
    conf: float       # 信頼度
    impl: dict        # 実装情報
    inverse_of: str|None  # 逆関数
```

**Catalog クラス:**
- 型と関数のカタログを管理
- 型グラフのインデックス構築（`by_cod`, `by_dom`）
- 効率的な関数検索

#### 探索アルゴリズム: `synthesize_backward`

**アルゴリズム概要:**

目的型 `src_type -> goal_type` に対して、**逆方向探索**を実行：

1. ゴール型 `goal_type` からスタート
2. `goal_type` を返す関数を探索
3. 各関数の `domain` を新しいサブゴールとする
4. `src_type` に到達したらパスを記録
5. コスト最小のパスから順に返す

**特徴:**
- Dijkstra的な最短経路探索（優先度付きキュー使用）
- コスト制限（`max_cost`）と探索ステップ制限（`max_steps`）
- 訪問済みノードの枝刈り

**擬似コード:**
```python
def synthesize_backward(catalog, src_type, goal_type, max_cost, max_steps):
    pq = [(0.0, 0.0, goal_type, [])]  # (est_cost, cum_cost, type, path)
    visited_best = {}
    results = []

    while pq and steps < max_steps:
        est_total, cum_cost, cur_type, path = heappop(pq)

        if cur_type == src_type:
            results.append((cum_cost, path))
            continue

        # 枝刈り
        if cum_cost >= visited_best.get(cur_type, inf):
            continue
        visited_best[cur_type] = cum_cost

        # 展開: cur_typeを返す関数を探索
        for f in catalog.funcs_returning(cur_type):
            new_cum = cum_cost + f.cost
            if new_cum <= max_cost:
                new_path = [f] + path  # 逆順で追加
                heappush(pq, (new_cum, new_cum, f.dom, new_path))

    return sorted(results, key=lambda x: x[0])
```

### 3. 実行スクリプト（run_prototype.py）

カタログを読み込み、指定された型変換を探索し、結果をJSON形式で出力。

**出力形式:**
```json
{
  "goal": "Product->CO2",
  "plans": [
    {
      "cost": 5.0,
      "confidence_est": 0.7056,
      "steps": [
        {"id": "usesEnergy", "sig": "Product -> Energy", "cost": 1.0, "conf": 0.9},
        {"id": "energyToFuelEstimate", "sig": "Energy -> Fuel", "cost": 3.0, "conf": 0.8},
        {"id": "fuelToCO2", "sig": "Fuel -> CO2", "cost": 1.0, "conf": 0.98}
      ],
      "proof": "usesEnergy ∘ energyToFuelEstimate ∘ fuelToCO2"
    }
  ]
}
```

**信頼度計算:**
関数の信頼度の積として計算：
```python
confidence = product([f.conf for f in path])
# 例: 0.9 × 0.8 × 0.98 = 0.7056
```

## 型理論的解釈

### 型充足（Type Inhabitation）

目的型 `Product -> CO2` を「充足する」値（proof term）を探索する問題として定式化。

**問題:** `Product -> CO2` という型を持つ値（関数合成）は存在するか？

**解:**
```
λp:Product. fuelToCO2(energyToFuelEstimate(usesEnergy(p))) : Product -> CO2
```

これは以下の型付けルールから導出される：

```
usesEnergy : Product -> Energy
energyToFuelEstimate : Energy -> Fuel
fuelToCO2 : Fuel -> CO2
───────────────────────────────────────────── (composition)
usesEnergy ∘ energyToFuelEstimate ∘ fuelToCO2 : Product -> CO2
```

### 中間型の出現

探索の過程で、以下の中間型が**自動的に導出**される：

1. **Goal**: `CO2` を生成する関数は？→ `fuelToCO2 : Fuel -> CO2`
2. **Subgoal**: `Fuel` を生成する関数は？→ `energyToFuelEstimate : Energy -> Fuel`
3. **Subgoal**: `Energy` を生成する関数は？→ `usesEnergy : Product -> Energy`
4. **Success**: 起点型 `Product` に到達

この過程で、`Energy` と `Fuel` という**隠れたブリッジ概念**が型制約から自動的に発見される。

## 圏論的解釈

### スパンの合成

各関数を射として、型グラフ上の経路を探索：

```
Product --usesEnergy--> Energy --energyToFuelEstimate--> Fuel --fuelToCO2--> CO2
```

これは以下のスパンの合成に対応：

```
Product ← Energy → Fuel
Fuel ← Fuel → CO2
```

Pullbackによって中間型が一致する場合のみ合成可能。

## 実装の特徴

### 利点

1. **宣言的**: YAMLで型と関数を簡潔に記述
2. **自動探索**: 目的型を与えるだけで変換パスを自動発見
3. **コスト最適化**: 最小コストのパスを優先的に探索
4. **信頼度計算**: 合成パスの信頼度を自動計算
5. **拡張可能**: 新しい型・関数の追加が容易

### 制限事項

1. **実行層未実装**: 現在は探索のみ。実際のSPARQL実行やREST呼び出しは未実装
2. **単位変換**: 単位の自動変換は未実装（手動で変換関数を定義する必要あり）
3. **ヒューリスティクス**: 現在は単純なDijkstra探索（A*のヒューリスティクスは未実装）

## 今後の拡張

### 短期（実装済み基盤の拡張）

1. **実行レイヤー**: SPARQL/REST/Formula の実際の実行
2. **単位変換**: 自動的な単位変換関数の挿入
3. **Provenance**: PROV-O形式での来歴記録

### 中期（アルゴリズム改善）

1. **A*探索**: ヒューリスティクス関数の導入
2. **双方向探索**: 起点と終点からの同時探索
3. **キャッシング**: 型到達可能性のキャッシュ

### 長期（理論的拡張）

1. **依存型**: 値に依存する型の導入
2. **証明項の検証**: Lean4等での形式検証
3. **多引数関数**: カリー化を超えた多引数サポート
4. **Cospan/Colimit**: オントロジー統合機能

## 参考文献

- `theory/span_cospan.md`: Span/Cospanによるオントロジー理論
- `theory/dsl_design.md`: DSL設計書
- `theory/cfp_example.md`: CFP例題の理論的解説
