いいですね — では **CFP（Carbon Footprint）計算を「type inhabitation（型充足）」問題として扱う専用 DSL** を（設計＋動作原理＋実例＋実装方針）で深掘りします。狙いは次の通り：

* オントロジー（型）と変換（関数）を明確に記述できる言語
* 目的型（例：`Product -> CO2`）が与えられたときに「どの関数列（合成パス）がその型を満たすか」を探索して実行プランを生成する
* 単位・不確かさ・コスト・逆像等を扱える（実務で必須）

以下は設計書＋具体例＋探索アルゴリズム＋実装提案です。長めですが、すぐにプロトタイプ化できるレベルで揃えます。

---

# 1. 主要アイデア（要約）

* 型 = オントロジーのクラス（`Product`, `Energy` 等）。型は**単位・レンジを含む精錬型**を持てる。
* 関数 = `f: A -> B`（関数カタログに登録）。関数は実装情報（REST/スクリプト）、逆像の有無、コスト、信頼度を持つ。
* 問い合わせ = 目的型 `Goal : A -> Z`（例 `Product -> CO2`）。
* 解 = 関数の合成列 `f_n ∘ ... ∘ f_1` で `A -> Z` を作ること（存在すれば証明項／実行プランを生成）。これが type inhabitation。
* 探索 = 型グラフ上での経路探索（逆探索やA*）＋逆像推定で穴を埋める。結果は実行可能なワークフロー（SPARQL + 関数呼出し）に変換。

---

# 2. DSL 概観（High-level concrete syntax）

簡潔で読みやすい YAML/mini-DSL を想定。例：

```
# types
type Product
type Energy [unit=J, range = >=0]
type Fuel   [unit=kg]
type CO2    [unit=kg]

# functions
fn usesEnergy {
  sig: Product -> Energy
  impl: sparql("SELECT ?p ?e WHERE { ?p :usesEnergy ?e }")
  cost: 1
  confidence: 0.9
}

fn fuelToEnergy {
  sig: Fuel -> Energy
  impl: rest("POST", "https://.../fuel_to_energy")
  cost: 2
  confidence: 0.95
}

fn fuelToCO2 {
  sig: Fuel -> CO2
  impl: formula("CO2 = fuel_amount * emission_factor")
  cost: 1
  confidence: 0.98
}

# inverse helper (optional)
fn energyToFuelEstimate {
  sig: Energy -> Fuel
  impl: formula("fuel = energy / efficiency")
  cost: 3
  confidence: 0.8
  inverse_of: fuelToEnergy
}
```

このDSLはそのまま Function Catalog と Type カタログになる。`impl` は実行方法（SPARQL、REST、式、MLモデル）を示す。

---

# 3. 型システム（概念）

* 基本型 `T`（例 `Product`）
* 精錬型 `T[r]`（例 `Energy[J]` または `Energy[>=0]`）
* 短射影：関数は単引数を想定する（多引数はカリー化）。
* サブタイプ：`ElectricalEnergy ≤ Energy` が可能（`rdfs:subClassOf` を反映）。
* 逆関数：`f` に `inverse_support` があれば、逆向きに探索できる（ただし不確かさ付き）。

内部表現は `GADT`/`ADT` で型ノードとエッジ（関数）を持つグラフ。

---

# 4. 証明項（Proof term）とプロヴェナンス

合成して得られた解は *証明項* を持つ：

```
productToCO2_proof(p) = fuelToCO2(energyToFuelEstimate(usesEnergy(p)))
```

証明項に含める情報：

* 使用した関数のIDとバージョン
* 入手したデータ（SPARQLで取った値）
* 単位変換のステップ
* 仮定（推定を使った場合の仮定値・信頼度）
* コスト合計・信頼度合成（信頼度は積や最小値などの合成則）

これを RDF/PROV-O 形式で帰り値に付ける。

---

# 5. 探索アルゴリズム（詳述）

## 5.1 問題定式化

Goal: `A -> Z`.
Given: graph `G = (V, E)` where `V` = types, `E` = functions with signature `dom -> cod`. Each `e` has metadata `(cost, confidence, impl, inverse_support)`.

Find a sequence `p = e_k ∘ ... ∘ e_1` such that `dom(e_1) = A` and `cod(e_k) = Z`. (If functions are curried, same idea.)

## 5.2 探索戦略（実装推奨）

* **逆探索（backward search）**：目的型 `Z` から始め、どの関数が `Z` を返せるかを見つけ、各関数の `dom` を次のゴールにする。CFPのように最終出力が数値であれば逆探索が効果的。
* **前方探索（forward search）**：ソース `A` から進めて `Z` に到達する経路を探す。ソースに多くのデータがある場合に有利。
* **ハイブリッド**：bidirectional search（両端探索）で効率化。
* **コスト最小化（A*）**：`f(n) = g(n) + h(n)` を使う。`g(n)` は累積コスト、`h(n)` は型ヒューリスティック（残りの距離推定） — 例えば構造的距離や信頼度から変換できる。
* **型一致の許容（approximate matching）**：部分型／単位異なる場合は許容ルールでマッチング（例：`Energy[J]` と `Energy[kWh]` は変換関数を挿入して一致）。

## 5.3 逆像（inverse）と穴埋め

多くの関数には逆が存在しない。逆がない場合の戦術：

1. **逆算関数（explicit inverse）**：`energyToFuelEstimate : Energy -> Fuel` があれば使う。
2. **補助手段（estimator）**：統計或いは ML モデルにフォールバック。これらは `confidence` が低い。
3. **外部データ探索**：KG や別オントロジーから `Fuel` を推定する。
4. **仮定（assumption）として提示**：ユーザーに仮定を確認させる（ただし自動化重視なら仮定をプロヴェナンスに明記）。

## 5.4 剪定（Pruning）

* 深さ制限（max_depth）
* コスト閾値（max_cost）
* 信頼度閾値（min_confidence）
* 同型・冗長パスの削除（canonicalization）
* キャッシュ（型 -> 到達可能な型集合）

## 5.5 証明と最終正規化

* 見つかった経路は式ツリーとして規格化（中間の単位変換を明示）
* 単位チェックを行い、必要なら単位変換ノードを追加（例えば `J ↔ kWh`）
* 信頼度合成（例 `overall_confidence = Π confidence_i` or `min`）とコスト合計を算出

---

# 6. DSL の型充足の例（CFPケース、詳細な導出）

## 登録済み要素（DSLでの定義）

```
type Product
type Energy [unit=J]
type Fuel   [unit=kg]
type CO2    [unit=kg]

fn usesEnergy { sig: Product -> Energy, impl: sparql(...), cost:1, conf:0.9 }
fn fuelToEnergy { sig: Fuel -> Energy, impl: formula(eff), cost:2, conf:0.95 }
fn fuelToCO2 { sig: Fuel -> CO2, impl: formula(emission_factor), cost:1, conf:0.98 }
fn energyToFuelEstimate { sig: Energy -> Fuel, impl: formula(fuel = energy/eff), cost:3, conf:0.8, inverse_of: fuelToEnergy }
```

## Goal: `Product -> CO2`

### 逆探索の流れ

1. ゴール `CO2` に到達できる関数を探す → `fuelToCO2 : Fuel -> CO2` 発見。
   新しいサブゴール：`Product -> Fuel` を作る（実際は `Product -> ?` で `? = Fuel` を目指す）
2. `Product -> Fuel` を作れる関数は直接ない → 間を埋める中間型を探す。
   候補の型 `Energy` がある（`usesEnergy : Product -> Energy` と `energyToFuelEstimate : Energy -> Fuel` がある）。
3. 合成パス： `Product -> Energy` (usesEnergy)  ∘ `Energy -> Fuel` (energyToFuelEstimate) ∘ `Fuel -> CO2` (fuelToCO2)
   合成すると `Product -> CO2` を得る。
4. 証明項（計算式）を合成して実行プランを作る。

### 実行プラン（擬似ワークフロー）

* SPARQL: get `energy_needed = usesEnergy(product)`
* Local calc: `fuel_needed = energy_needed / efficiency`（energyToFuelEstimate で使う efficiency はパラメータ）
* Local calc: `co2 = fuel_needed * emission_factor`
* Write back: `:product :hasCO2 ?co2 . prov:...`

### 信頼度・コスト

* overall_confidence = 0.9 * 0.8 * 0.98 = 0.7056（例：積で合成）
* total_cost = 1 + 3 + 1 = 5

この結果をユーザに返し、証明項とともにプロヴェナンスを保存する。

---

# 7. DSL の formal grammar（簡易BNF）

```
<spec> ::= { <type_decl> } { <fn_decl> }

<type_decl> ::= "type" <IDENT> [ "[" <attr_list> "]" ]
<attr_list> ::= <attr> { "," <attr> }
<attr> ::= "unit=" <UNIT> | "range=" <RANGE> | "subtype=" <IDENT>

<fn_decl> ::= "fn" <IDENT> "{" <fn_body> "}"
<fn_body> ::= "sig:" <type_expr> ";"
            "impl:" <impl_spec> ";"
            "cost:" <NUMBER> ";"
            "conf:" <NUMBER> [ ";" "inverse_of:" <IDENT> ] ";"

<type_expr> ::= <IDENT> "->" <IDENT>
<impl_spec> ::= "sparql(" <STRING> ")" | "rest(" <STRING> ")" | "formula(" <STRING> ")"
```

これは拡張可能。

---

# 8. 実装方針（プロトタイピングから本番まで）

## プロトタイプ（早い勝ち筋）

* 言語：Python（速い試作）または Haskell（型での安全性が高い）
* データストア：小規模なら in-memory graph、実運用は RDF triple store（GraphDB等）＋SPARQL
* 探索エンジン：逆探索ベースの A*（Python: heapq、Haskell: priority-queue）
* Function Catalog：YAML（DSL）→ロードして adjacency graph を作る
* 実行層：関数の `impl` はプラガブル（REST呼び出し、Python計算関数、外部ML）

## 型安全性を重視するなら

* Haskell + GADTs または Agda/Lean（依存型）で `Type` と `Func` を厳密にモデル化。
* Lean なら合成の正当性（単位保存など）を定理として証明できる（工数はかかる）。

## スケール/運用

* キャッシュ（型 -> 到達可能型）をRedis等に保存
* コスト・confidence をメタデータで管理して最適化
* ユーザ対話（仮定提示）とヒューマンインザループで精度を担保

---

# 9. 最低限の API/出力仕様（実装で必要なもの）

* `POST /synthesize` with `{ goal: "Product->CO2", source: { product: "urn:..." }, constraints: {...} }`
  returns `{ plan: [ step1, step2, ... ], proof: <proof-term>, cost, confidence, provenance }`
* `GET /catalog` returns Function Catalog (types, signatures, impl endpoints)
* `POST /execute` runs a plan and returns results + prov

---

# 10. 実装して動かすための短期ロードマップ（3ステップ）

1. **DSL & loader**（1 week）：YAMLベースの DSL と loader を作る（types + functions）。
2. **探索器（逆探索 A*）と正規化**（2–3 weeks）：入出力単位チェック、逆像サポート、証明項の生成。
3. **実行レイヤ**（2–4 weeks）：SPARQL呼び出し・関数実行・結果書き戻し・PROV生成。実データでCFPケースを回す。

---

# 11.注意点・落とし穴

* **逆像の不確かさ**：逆推論は常に推定。Provenanceとconfidenceを明確にする。
* **探索爆発**：経路数が爆発する。深さ制限・コストヒューリスティクス必須。
* **単位の過小評価**：単位不整合で誤った合成が起きやすい。単位は型の第一級属性にする。
* **意味的曖昧さ**：語彙揺れは事前の語彙整備・アライメントで減らす（スパン・pullbackベースが有効）。

---

# 12. 出力例（JSON） — `Product->CO2` の合成案（返却）

```json
{
  "goal": "Product->CO2",
  "plan": [
    { "step": 1, "fn": "usesEnergy", "input": "product:urn:123", "output": "energy:100000", "impl": "sparql(...)" },
    { "step": 2, "fn": "energyToFuelEstimate", "input": "energy:100000", "params": {"efficiency":0.35}, "output": "fuel:12.3", "impl": "formula(...)" },
    { "step": 3, "fn": "fuelToCO2", "input": "fuel:12.3", "output": "co2:33.2", "impl": "formula(...)" }
  ],
  "proof": "fuelToCO2(energyToFuelEstimate(usesEnergy(product)))",
  "cost": 5,
  "confidence": 0.7056,
  "provenance": {
    "steps": [
      {"fn":"usesEnergy","source":"KG:GraphDB","time":"2025-11-29T06:10:00Z"},
      {"fn":"energyToFuelEstimate","source":"localModel:v1.2"},
      {"fn":"fuelToCO2","source":"localFormula:ef_2024"}
    ]
  }
}
```

---

# 13. まとめ（提案）

* この DSL は **オントロジー（NGSI-LD/RDF）をそのまま「型」として読み込み、関数カタログを型付き関数群として置く** 設計が自然で実装性が高い。
* 探索は **逆探索＋A*** のハイブリッドが現実的。逆像は明示的な `inverse` 関数か推定モデルで補う。
* 重要：**単位・信頼度・プロヴェナンス** を型/メタデータで一貫して扱うこと。

---

もしご希望なら、次のどれかをすぐ作ります（実行可能なアウトプットを生成します）：

A. 上のDSLサンプル（YAML）を実際のCFP要素で埋めた `catalog.yaml` を作る。
B. Pythonでの簡易プロトタイプ（DSLローダー＋逆探索 A* の最短実装）を書いて、上のCFP例で動かす。
C. Haskell（GADT）で型安全なモデルのスケルトンを書き、合成関数の型チェックを示す。

どれを作りましょう？（あなたが選ばなくても、Aをそのまま作ることもできます — ただしここで即座に作るためには選択してください。）
