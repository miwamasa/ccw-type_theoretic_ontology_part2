# CFP計算の型理論的解題

## 問題設定

**目標**: 製品（Product）のカーボンフットプリント（CO2排出量）を計算する

**制約**:
- 直接的な `Product -> CO2` の関数は存在しない
- 利用可能な関数は断片的（部分的なマッピングのみ）
- コストと信頼度を考慮した最適パスを見つける必要がある

**入力カタログ**:

```yaml
types:
  - Product   # 製品
  - Energy    # エネルギー（単位: J）
  - Fuel      # 燃料（単位: kg）
  - CO2       # 二酸化炭素（単位: kg）

functions:
  - usesEnergy: Product -> Energy (cost=1, conf=0.9)
  - fuelToEnergy: Fuel -> Energy (cost=2, conf=0.95)
  - fuelToCO2: Fuel -> CO2 (cost=1, conf=0.98)
  - energyToFuelEstimate: Energy -> Fuel (cost=3, conf=0.8, inverse)
```

---

## 解法1: 型理論的アプローチ

### 型充足問題としての定式化

**問い**: 型 `Product -> CO2` を持つ項（term）は存在するか？

**与えられた公理（axioms）**:
```
Γ ⊢ usesEnergy : Product → Energy
Γ ⊢ energyToFuelEstimate : Energy → Fuel
Γ ⊢ fuelToCO2 : Fuel → CO2
```

### 型導出（Type Derivation）

**目標型**: `Product → CO2`

**導出過程**:

```
(1) Γ ⊢ usesEnergy : Product → Energy          [公理]
(2) Γ ⊢ energyToFuelEstimate : Energy → Fuel   [公理]
(3) Γ ⊢ fuelToCO2 : Fuel → CO2                 [公理]

(4) Γ ⊢ (energyToFuelEstimate ∘ usesEnergy) : Product → Fuel
    [合成則: (1), (2)]

(5) Γ ⊢ (fuelToCO2 ∘ energyToFuelEstimate ∘ usesEnergy) : Product → CO2
    [合成則: (3), (4)]
```

**証明項（Proof Term）**:

```haskell
productToCO2 :: Product -> CO2
productToCO2 = fuelToCO2 . energyToFuelEstimate . usesEnergy
```

または、λ式で：

```
λp:Product. fuelToCO2(energyToFuelEstimate(usesEnergy(p)))
```

### 型判定

この項の型は、関数合成の型付けルールから導出される：

```
f : A → B    g : B → C
─────────────────────── [Composition]
g ∘ f : A → C
```

**適用**:
```
usesEnergy : Product → Energy
energyToFuelEstimate : Energy → Fuel
────────────────────────────────────────
energyToFuelEstimate ∘ usesEnergy : Product → Fuel

energyToFuelEstimate ∘ usesEnergy : Product → Fuel
fuelToCO2 : Fuel → CO2
──────────────────────────────────────────────────
fuelToCO2 ∘ energyToFuelEstimate ∘ usesEnergy : Product → CO2  ✓
```

---

## 解法2: 圏論的アプローチ（Span合成）

### 型グラフの構造

```
Product --usesEnergy--> Energy --energyToFuelEstimate--> Fuel --fuelToCO2--> CO2
```

### Spanとしての表現

各関数をspanとして表現：

**Span 1**: Product ← Product → Energy
```
Product ← Product → Energy
  (id)    (usesEnergy)
```

**Span 2**: Energy ← Energy → Fuel
```
Energy ← Energy → Fuel
 (id)   (energyToFuelEstimate)
```

**Span 3**: Fuel ← Fuel → CO2
```
Fuel ← Fuel → CO2
(id)   (fuelToCO2)
```

### Pullback による合成

**Span 1 と Span 2 の合成**:

```
Product ← Product → Energy
            |
         pullback
            |
        Energy ← Energy → Fuel
```

Pullback により：
```
Product ← Product×Energy Energy → Fuel
```

中間型 `Energy` が一致するため、pullback は自明に：
```
Product ← Product → Fuel
```

**これと Span 3 の合成**:

```
Product ← Product → Fuel
            |
         pullback
            |
          Fuel ← Fuel → CO2
```

最終結果：
```
Product ← Product → CO2
```

これは求める射 `Product → CO2` に対応。

### 圏論的解釈の意義

Pullbackによる合成は、**型が一致する場合にのみ合成可能**という制約を自動的に保証する。これにより：

- 意味的に互換性のある変換のみが接続される
- 型安全性が保たれる
- 誤った合成が排除される

---

## 解法3: グラフ探索アプローチ

### 問題のグラフ表現

**ノード（型）**: {Product, Energy, Fuel, CO2}

**エッジ（関数）**:
```
Product --[1, 0.9]--> Energy
Energy --[3, 0.8]--> Fuel
Fuel --[2, 0.95]--> Energy
Fuel --[1, 0.98]--> CO2
```

エッジラベル: [コスト, 信頼度]

### 逆方向探索（Backward Search）

**アルゴリズム**: ゴールから逆向きに探索

**初期状態**:
- ゴール = CO2
- ソース = Product
- 優先度キュー = [(0, CO2, [])]

**探索過程**:

```
ステップ 1: ノード = CO2, パス = []
  → CO2 を返す関数を探す
  → fuelToCO2 : Fuel -> CO2 を発見
  → 新しいゴール = Fuel
  → キューに追加: (1, Fuel, [fuelToCO2])

ステップ 2: ノード = Fuel, パス = [fuelToCO2]
  → Fuel を返す関数を探す
  → energyToFuelEstimate : Energy -> Fuel を発見
  → 新しいゴール = Energy
  → キューに追加: (4, Energy, [energyToFuelEstimate, fuelToCO2])

ステップ 3: ノード = Energy, パス = [energyToFuelEstimate, fuelToCO2]
  → Energy を返す関数を探す
  → usesEnergy : Product -> Energy を発見
  → ゴールに到達！Product == Product
  → 解を記録: (5, [usesEnergy, energyToFuelEstimate, fuelToCO2])
```

**発見されたパス**:
```
Product --usesEnergy--> Energy --energyToFuelEstimate--> Fuel --fuelToCO2--> CO2
```

**パスのコスト**: 1 + 3 + 1 = 5
**パスの信頼度**: 0.9 × 0.8 × 0.98 = 0.7056

---

## 解の詳細分析

### パスの構造

```
Product
   |
   | [1] usesEnergy (0.9)
   | "製品がどれだけエネルギーを使用するかをKGから取得"
   ↓
Energy
   |
   | [2] energyToFuelEstimate (0.8) ⚠️ inverse
   | "エネルギー量から燃料使用量を逆算（推定）"
   ↓
Fuel
   |
   | [3] fuelToCO2 (0.98)
   | "燃料燃焼による CO2 排出量を計算"
   ↓
CO2
```

### 各ステップの意味

#### ステップ1: Product → Energy (usesEnergy)

**実装**: SPARQL クエリ
```sparql
SELECT ?p ?e WHERE {
  ?p :usesEnergy ?e
}
```

**意味**: 知識グラフから製品のエネルギー使用量を取得

**コスト**: 1（SPARQLクエリ1回）

**信頼度**: 0.9（KGのデータ品質に依存）

#### ステップ2: Energy → Fuel (energyToFuelEstimate)

**実装**: 数式（逆算）
```
fuel = energy / efficiency
```

**意味**: エネルギー量から必要な燃料量を推定

**注意**: これは逆関数（`fuelToEnergy` の逆）であり、`efficiency` パラメータが必要

**コスト**: 3（逆算は不確実性が高いため高コスト）

**信頼度**: 0.8（推定であることを反映）

**問題点**:
- 効率パラメータ（efficiency）が必要
- 燃料の種類が特定できない（ガソリン？ディーゼル？）
- 推定に基づくため誤差が大きい可能性

#### ステップ3: Fuel → CO2 (fuelToCO2)

**実装**: 数式
```
co2 = fuel_amount * emission_factor
```

**意味**: 燃料燃焼による CO2 排出量を計算

**パラメータ**:
- `fuel_amount`: ステップ2の出力
- `emission_factor`: 燃料の種類による排出係数（例: 2.7 kg-CO2/kg-fuel）

**コスト**: 1（単純な計算）

**信頼度**: 0.98（排出係数は科学的に確立）

---

## メトリクスの分析

### コスト分析

**総コスト**: 5.0

**コスト内訳**:
- usesEnergy: 1.0 (20%)
- energyToFuelEstimate: 3.0 (60%) ← 支配的
- fuelToCO2: 1.0 (20%)

**考察**:
- 逆算ステップ（energyToFuelEstimate）がコストの60%を占める
- これは推定の不確実性を反映
- より直接的なパスがあれば、コストを削減できる可能性

### 信頼度分析

**総信頼度**: 0.7056 ≈ 70.56%

**信頼度内訳**（対数スケール）:
- usesEnergy: 0.9 (-10.5% からの減少)
- energyToFuelEstimate: 0.8 (-20% からの減少) ← 最大の信頼度損失
- fuelToCO2: 0.98 (-2% からの減少)

**考察**:
- 信頼度の積なので、各ステップの不確実性が累積
- energyToFuelEstimate が最大のボトルネック
- 70.56% は実用的には許容範囲だが、重要な意思決定には追加検証が必要

---

## 代替パスの検討

### 存在しないが望ましいパス

#### 理想的なパス 1: 直接マッピング
```
Product --productToCO2--> CO2
```
- コスト: 1（想定）
- 信頼度: 高い（直接測定）
- **問題**: このような関数は通常カタログに存在しない

#### 理想的なパス 2: 燃料経由
```
Product --usesFuel--> Fuel --fuelToCO2--> CO2
```
- コスト: 2（推定）
- 信頼度: 0.98（推定、逆算なし）
- **問題**: `usesFuel` 関数がカタログに存在しない

### 現在のカタログでの代替パス

現在のカタログでは、`Product -> CO2` への**唯一のパス**が発見されたパスである。

他のパスの可能性：
```
Product -> Energy -> Fuel -> Energy -> Fuel -> ... (循環)
```

しかし、訪問済みノードの枝刈りにより、循環は排除される。

---

## 中間型の出現メカニズム

### 隠れたブリッジ概念の発見

**最初の状態**: Product と CO2 の間に明示的な関係なし

**探索過程**:

1. **CO2 への入口を探す**
   - `fuelToCO2` を発見
   - → `Fuel` が CO2 へのゲートウェイと判明

2. **Fuel への経路を探す**
   - `energyToFuelEstimate` を発見
   - → `Energy` が Fuel へのブリッジと判明

3. **Product から Energy への接続**
   - `usesEnergy` を発見
   - → 完全な経路が構築される

### ブリッジ概念の役割

**Energy**:
- Product から取得可能（usesEnergy）
- Fuel への変換可能（energyToFuelEstimate）
- → **第1のブリッジ**

**Fuel**:
- Energy から導出可能（energyToFuelEstimate）
- CO2 への変換可能（fuelToCO2）
- → **第2のブリッジ（最終ブリッジ）**

この二段階のブリッジ構造は、**探索によって初めて明らかになる**。これが `theory/cfp_example.md` で説明されている「見えていなかった中間段階が探索によって徐々に明らかになる」現象である。

---

## 型理論的考察

### 型の精錬（Refinement Types）

各型には単位情報が付加されている：

```
Energy [unit=J, range=>=0]
Fuel [unit=kg]
CO2 [unit=kg]
```

これは**精錬型（Refinement Types）**の一種である。

### 単位の整合性

**パス全体の単位変換**:

```
Product (無次元) → Energy [J] → Fuel [kg] → CO2 [kg]
```

**単位変換の妥当性**:
- Product → Energy: エネルギー消費量（J）
- Energy → Fuel: エネルギー密度の逆（kg/J = 1/(J/kg)）
- Fuel → CO2: 排出係数（kg-CO2/kg-fuel、つまり無次元または kg/kg）

最終的に CO2 [kg] が得られる。

### 依存型への拡張可能性

より高度な型システムでは：

```haskell
energyToFuelEstimate : (e : Energy) -> Fuel { f | f * energyDensity ≈ e }
```

このような依存型により、値レベルの制約（エネルギー保存則など）を型システムで表現できる。

---

## 実行プランの構築

### 擬似コード

```python
def compute_product_cfp(product_uri):
    # Step 1: Product -> Energy
    energy = usesEnergy(product_uri)
    # SPARQL: SELECT ?e WHERE { <product_uri> :usesEnergy ?e }
    # Result: energy = 100000 [J]

    # Step 2: Energy -> Fuel
    efficiency = 0.35  # パラメータ（要指定）
    fuel = energy / efficiency
    # Result: fuel = 100000 / 0.35 ≈ 285714 [J] / (J/kg) = ... [kg]
    # Actually: fuel = energy / energy_density
    # Assuming energy_density = 42 MJ/kg (gasoline)
    fuel = energy / (42 * 1e6)  # [J] / [J/kg] = [kg]
    # Result: fuel ≈ 0.00238 [kg]

    # Step 3: Fuel -> CO2
    emission_factor = 2.7  # kg-CO2/kg-fuel (gasoline)
    co2 = fuel * emission_factor
    # Result: co2 ≈ 0.00643 [kg] = 6.43 [g]

    return co2
```

### 実行例（数値例）

**入力**:
- Product URI: `urn:product:laptop`
- KG に保存された情報: `:laptop :usesEnergy "360000"^^xsd:float` (100 Wh = 360000 J)

**実行**:

```
Step 1: usesEnergy(urn:product:laptop)
  SPARQL → energy = 360000 J (= 100 Wh)

Step 2: energyToFuelEstimate(360000 J)
  Assuming gasoline: energy_density = 42 MJ/kg
  fuel = 360000 / (42 * 1e6) = 0.00857 kg = 8.57 g

Step 3: fuelToCO2(0.00857 kg)
  Assuming gasoline: emission_factor = 2.7 kg-CO2/kg
  co2 = 0.00857 * 2.7 = 0.02314 kg = 23.14 g
```

**結果**: ノートPCの製造エネルギー相当の CO2 排出量 ≈ **23.14 g CO2**

（注: これは極めて単純化された例であり、実際の CFP 計算ははるかに複雑）

---

## Provenance（来歴）の記録

### PROV-O形式での記録

```turtle
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix ex: <http://example.org/> .

ex:cfp_result_123
  a prov:Entity ;
  prov:value "23.14"^^xsd:float ;
  prov:wasGeneratedBy ex:cfp_computation_456 .

ex:cfp_computation_456
  a prov:Activity ;
  prov:used ex:laptop_energy_data ;
  prov:qualifiedAssociation [
    a prov:Association ;
    prov:agent ex:synthesis_engine ;
    prov:hadPlan ex:plan_product_to_co2
  ] .

ex:plan_product_to_co2
  a prov:Plan ;
  prov:value "usesEnergy ∘ energyToFuelEstimate ∘ fuelToCO2" ;
  ex:totalCost "5.0"^^xsd:float ;
  ex:confidence "0.7056"^^xsd:float .

ex:laptop_energy_data
  a prov:Entity ;
  prov:wasAttributedTo ex:knowledge_graph_v1 ;
  prov:generatedAtTime "2025-11-29T12:00:00Z"^^xsd:dateTime .
```

---

## 改善案

### 信頼度向上のための改善

1. **直接的な燃料使用量データの取得**
   - 新しい関数: `usesFuel : Product -> Fuel` をカタログに追加
   - これにより逆算ステップを回避し、信頼度を向上

2. **複数パスの平均**
   - 複数の異なるパスで計算し、結果を平均または信頼度加重平均
   - 不確実性の定量化

3. **パラメータの明示的な指定**
   - `efficiency`, `emission_factor` を Product の属性として KG に保存
   - 推定ではなく実測値を使用

### コスト削減のための改善

1. **直接マッピングの追加**
   - 頻繁に使用されるパスを直接関数として定義
   - 例: `productCFP : Product -> CO2` を計算済みの値として保存

2. **キャッシング**
   - 一度計算した結果をキャッシュ
   - 同じ製品の再計算を避ける

### アルゴリズムの改善

1. **A* ヒューリスティクス**
   - 型の構造的距離をヒューリスティクスとして使用
   - 探索効率の向上

2. **複数解の提示**
   - コスト最小だけでなく、信頼度最大のパスも提示
   - ユーザーがトレードオフを選択

---

## 結論

### 解の妥当性

発見されたパス `Product → Energy → Fuel → CO2` は：

- ✓ 型理論的に健全（型導出が正しい）
- ✓ 圏論的に妥当（スパン合成が成立）
- ✓ アルゴリズム的に最適（最小コスト）
- ✓ 実用的に意味がある（物理的に解釈可能）

### 制限事項

- ⚠️ 逆算ステップ（Energy → Fuel）が推定に依存
- ⚠️ パラメータ（efficiency, emission_factor）が外部から必要
- ⚠️ 単一パスのみ（代替パスが存在しない）
- ⚠️ 信頼度 70.56% は重要な意思決定には不十分な場合も

### 理論的意義

この解題は、以下を実証している：

1. **型理論の実用性**: 抽象的な型理論が実際の問題（CFP計算）に適用可能
2. **中間型の自動発見**: 探索によって `Energy` と `Fuel` という隠れたブリッジが発見される
3. **スパン合成の実装可能性**: 圏論的な概念が実際のコードとして動作
4. **メトリクスの合成**: コストと信頼度が自然に合成される

### 実用化への道筋

本解題で示された手法を実用化するには：

1. カタログの拡充（より多くの型と関数）
2. 実行レイヤーの実装（SPARQL/REST/Formula の実際の実行）
3. パラメータ管理機構（efficiency 等の動的取得）
4. 不確実性の定量化（信頼区間の計算）
5. ユーザーインターフェース（パスの可視化、パラメータ調整）

これらの拡張により、理論的な概念実証から実用的なシステムへと発展させることができる。
