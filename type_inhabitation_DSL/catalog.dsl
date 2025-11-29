# CFP (Carbon Footprint) 計算用カタログ
# 型理論ベースオントロジー合成システム DSL

# ========================================
# 型定義 (Type Declarations)
# ========================================

type Product

type Energy [unit=J, range=>=0]

type Fuel [unit=kg]

type CO2 [unit=kg]


# ========================================
# 関数定義 (Function Declarations)
# ========================================

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
